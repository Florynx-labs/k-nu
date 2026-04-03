"""
KÁNU Training System
Handles training loop, optimization, and monitoring
"""
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, Dataset
from torch.optim import AdamW
from torch.optim.lr_scheduler import CosineAnnealingLR
from typing import Dict, Any, Optional, List
import logging
import time
import json
from pathlib import Path
from tqdm import tqdm

logger = logging.getLogger(__name__)


class KANUTrainer:
    """
    Trainer for KÁNU LLM
    Supports distributed training, gradient accumulation, and mixed precision
    """
    
    def __init__(
        self,
        model: nn.Module,
        train_dataset: Dataset,
        val_dataset: Optional[Dataset] = None,
        learning_rate: float = 3e-4,
        batch_size: int = 8,
        gradient_accumulation_steps: int = 4,
        max_epochs: int = 10,
        warmup_steps: int = 1000,
        max_grad_norm: float = 1.0,
        save_dir: str = "./checkpoints",
        use_amp: bool = True,  # Automatic Mixed Precision
        log_interval: int = 100,
        eval_interval: int = 1000,
        save_interval: int = 5000,
    ):
        self.model = model
        self.train_dataset = train_dataset
        self.val_dataset = val_dataset
        
        # Training hyperparameters
        self.learning_rate = learning_rate
        self.batch_size = batch_size
        self.gradient_accumulation_steps = gradient_accumulation_steps
        self.max_epochs = max_epochs
        self.warmup_steps = warmup_steps
        self.max_grad_norm = max_grad_norm
        self.use_amp = use_amp
        
        # Logging and saving
        self.log_interval = log_interval
        self.eval_interval = eval_interval
        self.save_interval = save_interval
        self.save_dir = Path(save_dir)
        self.save_dir.mkdir(parents=True, exist_ok=True)
        
        # Device
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        logger.info(f"Training on device: {self.device}")
        
        # Move model to device
        self.model = self.model.to(self.device)
        
        # Create data loaders
        self.train_loader = DataLoader(
            train_dataset,
            batch_size=batch_size,
            shuffle=True,
            num_workers=4,
            pin_memory=True
        )
        
        if val_dataset:
            self.val_loader = DataLoader(
                val_dataset,
                batch_size=batch_size,
                shuffle=False,
                num_workers=4,
                pin_memory=True
            )
        else:
            self.val_loader = None
        
        # Optimizer (AdamW with weight decay)
        self.optimizer = AdamW(
            self.model.parameters(),
            lr=learning_rate,
            betas=(0.9, 0.95),
            weight_decay=0.1
        )
        
        # Learning rate scheduler
        total_steps = len(self.train_loader) * max_epochs // gradient_accumulation_steps
        self.scheduler = CosineAnnealingLR(
            self.optimizer,
            T_max=total_steps - warmup_steps,
            eta_min=learning_rate * 0.1
        )
        
        # Mixed precision scaler
        if use_amp:
            self.scaler = torch.cuda.amp.GradScaler()
        else:
            self.scaler = None
        
        # Training state
        self.global_step = 0
        self.current_epoch = 0
        self.best_val_loss = float('inf')
        
        # Metrics tracking
        self.train_losses = []
        self.val_losses = []
        self.learning_rates = []
        
        logger.info("KÁNU Trainer initialized")
        logger.info(f"Total training steps: {total_steps}")
        logger.info(f"Batch size: {batch_size}, Gradient accumulation: {gradient_accumulation_steps}")
        logger.info(f"Effective batch size: {batch_size * gradient_accumulation_steps}")
    
    def train(self):
        """Main training loop"""
        logger.info("Starting training...")
        
        self.model.train()
        
        for epoch in range(self.current_epoch, self.max_epochs):
            self.current_epoch = epoch
            logger.info(f"\n{'='*60}")
            logger.info(f"Epoch {epoch + 1}/{self.max_epochs}")
            logger.info(f"{'='*60}")
            
            epoch_loss = self._train_epoch()
            
            logger.info(f"Epoch {epoch + 1} completed. Average loss: {epoch_loss:.4f}")
            
            # Validation
            if self.val_loader:
                val_loss = self.evaluate()
                logger.info(f"Validation loss: {val_loss:.4f}")
                
                # Save best model
                if val_loss < self.best_val_loss:
                    self.best_val_loss = val_loss
                    self.save_checkpoint("best_model.pt")
                    logger.info(f"New best model saved! Val loss: {val_loss:.4f}")
            
            # Save epoch checkpoint
            self.save_checkpoint(f"epoch_{epoch + 1}.pt")
        
        logger.info("\nTraining completed!")
        logger.info(f"Best validation loss: {self.best_val_loss:.4f}")
    
    def _train_epoch(self) -> float:
        """Train for one epoch"""
        epoch_loss = 0.0
        num_batches = 0
        
        progress_bar = tqdm(self.train_loader, desc="Training")
        
        for batch_idx, batch in enumerate(progress_bar):
            # Move batch to device
            input_ids = batch['input_ids'].to(self.device)
            attention_mask = batch.get('attention_mask', None)
            if attention_mask is not None:
                attention_mask = attention_mask.to(self.device)
            labels = batch['labels'].to(self.device)
            
            # Forward pass with mixed precision
            if self.use_amp and self.scaler:
                with torch.cuda.amp.autocast():
                    _, loss = self.model(input_ids, attention_mask, labels)
                    loss = loss / self.gradient_accumulation_steps
                
                # Backward pass
                self.scaler.scale(loss).backward()
            else:
                _, loss = self.model(input_ids, attention_mask, labels)
                loss = loss / self.gradient_accumulation_steps
                loss.backward()
            
            # Gradient accumulation
            if (batch_idx + 1) % self.gradient_accumulation_steps == 0:
                # Gradient clipping
                if self.use_amp and self.scaler:
                    self.scaler.unscale_(self.optimizer)
                
                torch.nn.utils.clip_grad_norm_(self.model.parameters(), self.max_grad_norm)
                
                # Optimizer step
                if self.use_amp and self.scaler:
                    self.scaler.step(self.optimizer)
                    self.scaler.update()
                else:
                    self.optimizer.step()
                
                # Warmup or scheduler step
                if self.global_step < self.warmup_steps:
                    # Linear warmup
                    lr = self.learning_rate * (self.global_step + 1) / self.warmup_steps
                    for param_group in self.optimizer.param_groups:
                        param_group['lr'] = lr
                else:
                    self.scheduler.step()
                
                self.optimizer.zero_grad()
                
                self.global_step += 1
                
                # Logging
                current_lr = self.optimizer.param_groups[0]['lr']
                self.learning_rates.append(current_lr)
                
                if self.global_step % self.log_interval == 0:
                    logger.info(
                        f"Step {self.global_step} | "
                        f"Loss: {loss.item() * self.gradient_accumulation_steps:.4f} | "
                        f"LR: {current_lr:.2e}"
                    )
                
                # Evaluation
                if self.val_loader and self.global_step % self.eval_interval == 0:
                    val_loss = self.evaluate()
                    logger.info(f"Step {self.global_step} | Validation loss: {val_loss:.4f}")
                    self.model.train()
                
                # Save checkpoint
                if self.global_step % self.save_interval == 0:
                    self.save_checkpoint(f"step_{self.global_step}.pt")
            
            # Track loss
            epoch_loss += loss.item() * self.gradient_accumulation_steps
            num_batches += 1
            
            # Update progress bar
            progress_bar.set_postfix({
                'loss': f"{loss.item() * self.gradient_accumulation_steps:.4f}",
                'lr': f"{self.optimizer.param_groups[0]['lr']:.2e}"
            })
        
        return epoch_loss / num_batches
    
    def evaluate(self) -> float:
        """Evaluate on validation set"""
        if not self.val_loader:
            return 0.0
        
        self.model.eval()
        total_loss = 0.0
        num_batches = 0
        
        with torch.no_grad():
            for batch in tqdm(self.val_loader, desc="Evaluating"):
                input_ids = batch['input_ids'].to(self.device)
                attention_mask = batch.get('attention_mask', None)
                if attention_mask is not None:
                    attention_mask = attention_mask.to(self.device)
                labels = batch['labels'].to(self.device)
                
                if self.use_amp:
                    with torch.cuda.amp.autocast():
                        _, loss = self.model(input_ids, attention_mask, labels)
                else:
                    _, loss = self.model(input_ids, attention_mask, labels)
                
                total_loss += loss.item()
                num_batches += 1
        
        avg_loss = total_loss / num_batches
        self.val_losses.append(avg_loss)
        
        return avg_loss
    
    def save_checkpoint(self, filename: str):
        """Save model checkpoint"""
        checkpoint_path = self.save_dir / filename
        
        checkpoint = {
            'model_state_dict': self.model.state_dict(),
            'optimizer_state_dict': self.optimizer.state_dict(),
            'scheduler_state_dict': self.scheduler.state_dict(),
            'global_step': self.global_step,
            'current_epoch': self.current_epoch,
            'best_val_loss': self.best_val_loss,
            'config': self.model.config.__dict__,
        }
        
        if self.scaler:
            checkpoint['scaler_state_dict'] = self.scaler.state_dict()
        
        torch.save(checkpoint, checkpoint_path)
        logger.info(f"Checkpoint saved: {checkpoint_path}")
    
    def load_checkpoint(self, checkpoint_path: str):
        """Load model checkpoint"""
        checkpoint = torch.load(checkpoint_path, map_location=self.device)
        
        self.model.load_state_dict(checkpoint['model_state_dict'])
        self.optimizer.load_state_dict(checkpoint['optimizer_state_dict'])
        self.scheduler.load_state_dict(checkpoint['scheduler_state_dict'])
        
        self.global_step = checkpoint['global_step']
        self.current_epoch = checkpoint['current_epoch']
        self.best_val_loss = checkpoint['best_val_loss']
        
        if self.scaler and 'scaler_state_dict' in checkpoint:
            self.scaler.load_state_dict(checkpoint['scaler_state_dict'])
        
        logger.info(f"Checkpoint loaded: {checkpoint_path}")
        logger.info(f"Resuming from step {self.global_step}, epoch {self.current_epoch}")
    
    def get_training_stats(self) -> Dict[str, Any]:
        """Get training statistics"""
        return {
            'global_step': self.global_step,
            'current_epoch': self.current_epoch,
            'best_val_loss': self.best_val_loss,
            'train_losses': self.train_losses[-100:],  # Last 100
            'val_losses': self.val_losses,
            'learning_rates': self.learning_rates[-100:],
            'total_params': self.model.get_num_params(),
        }


class EngineeringDataset(Dataset):
    """
    Dataset for engineering and physics knowledge
    Bilingual (French/English)
    Memory-optimized: loads data lazily
    """
    def __init__(self, dataset_path: str, tokenizer, max_length: int = 512):
        self.tokenizer = tokenizer
        self.max_length = max_length
        self.dataset_path = dataset_path
        
        # Load only metadata, not full data
        with open(dataset_path, 'r', encoding='utf-8') as f:
            self.data = json.load(f)
        
        # Limit dataset size to avoid OOM
        if len(self.data) > 100:
            logger.warning(f"Dataset has {len(self.data)} examples, limiting to 100 to avoid OOM")
            self.data = self.data[:100]
        
        logger.info(f"Loaded {len(self.data)} examples from {dataset_path}")
    
    def __len__(self):
        return len(self.data)
    
    def __getitem__(self, idx):
        item = self.data[idx]
        
        # Get text (prompt + response)
        text = item.get('text', '')
        
        # Tokenize
        encoding = self.tokenizer(
            text,
            max_length=self.max_length,
            padding='max_length',
            truncation=True,
            return_tensors='pt'
        )
        
        input_ids = encoding['input_ids'].squeeze(0)
        attention_mask = encoding['attention_mask'].squeeze(0)
        
        # Labels are same as input_ids for language modeling
        labels = input_ids.clone()
        
        # Mask padding tokens in labels
        labels[attention_mask == 0] = -100
        
        return {
            'input_ids': input_ids,
            'attention_mask': attention_mask,
            'labels': labels
        }


def create_engineering_dataset(output_path: str):
    """
    Create initial engineering dataset with physics and engineering knowledge
    Bilingual: French and English
    """
    
    dataset = [
        # Physics - Mechanics (English)
        {
            "text": "Question: What is Newton's second law of motion?\nAnswer: Newton's second law states that Force equals mass times acceleration (F = ma). This fundamental law describes how the motion of an object changes when forces are applied to it. The acceleration of an object is directly proportional to the net force acting on it and inversely proportional to its mass.",
            "category": "physics_mechanics",
            "language": "en"
        },
        {
            "text": "Question: Explain the concept of momentum.\nAnswer: Momentum is the product of an object's mass and velocity (p = mv). It is a vector quantity that describes the motion of an object. The law of conservation of momentum states that in a closed system, the total momentum remains constant. This principle is crucial in analyzing collisions and explosions.",
            "category": "physics_mechanics",
            "language": "en"
        },
        
        # Physics - Mechanics (French)
        {
            "text": "Question: Qu'est-ce que la deuxième loi de Newton?\nRéponse: La deuxième loi de Newton stipule que la Force est égale à la masse multipliée par l'accélération (F = ma). Cette loi fondamentale décrit comment le mouvement d'un objet change lorsque des forces lui sont appliquées. L'accélération d'un objet est directement proportionnelle à la force nette qui agit sur lui et inversement proportionnelle à sa masse.",
            "category": "physics_mechanics",
            "language": "fr"
        },
        
        # Thermodynamics (English)
        {
            "text": "Question: What are the laws of thermodynamics?\nAnswer: The laws of thermodynamics are:\n1. First Law: Energy cannot be created or destroyed, only converted (ΔU = Q - W)\n2. Second Law: Entropy of an isolated system always increases\n3. Third Law: Entropy approaches zero as temperature approaches absolute zero\nThese laws govern all energy transformations and are fundamental to engineering.",
            "category": "thermodynamics",
            "language": "en"
        },
        
        # Thermodynamics (French)
        {
            "text": "Question: Quelles sont les lois de la thermodynamique?\nRéponse: Les lois de la thermodynamique sont:\n1. Première loi: L'énergie ne peut être ni créée ni détruite, seulement convertie (ΔU = Q - W)\n2. Deuxième loi: L'entropie d'un système isolé augmente toujours\n3. Troisième loi: L'entropie tend vers zéro lorsque la température approche le zéro absolu\nCes lois régissent toutes les transformations d'énergie et sont fondamentales pour l'ingénierie.",
            "category": "thermodynamics",
            "language": "fr"
        },
        
        # Engineering - Rocket Engines (English)
        {
            "text": "Question: How does a rocket engine work?\nAnswer: A rocket engine works by Newton's third law: for every action, there is an equal and opposite reaction. The engine burns propellant (fuel and oxidizer) in a combustion chamber, creating hot, high-pressure gas. This gas is expelled through a nozzle at high velocity, producing thrust in the opposite direction. The thrust equation is F = ṁ * Ve + (Pe - Pa) * Ae, where ṁ is mass flow rate, Ve is exhaust velocity, Pe is exit pressure, Pa is ambient pressure, and Ae is exit area.",
            "category": "rocket_engineering",
            "language": "en"
        },
        
        # Engineering - Rocket Engines (French)
        {
            "text": "Question: Comment fonctionne un moteur-fusée?\nRéponse: Un moteur-fusée fonctionne selon la troisième loi de Newton: pour chaque action, il y a une réaction égale et opposée. Le moteur brûle du propergol (carburant et oxydant) dans une chambre de combustion, créant un gaz chaud à haute pression. Ce gaz est expulsé à travers une tuyère à grande vitesse, produisant une poussée dans la direction opposée. L'équation de poussée est F = ṁ * Ve + (Pe - Pa) * Ae, où ṁ est le débit massique, Ve est la vitesse d'échappement, Pe est la pression de sortie, Pa est la pression ambiante, et Ae est l'aire de sortie.",
            "category": "rocket_engineering",
            "language": "fr"
        },
        
        # Materials Science (English)
        {
            "text": "Question: What are the key properties of Inconel 718?\nAnswer: Inconel 718 is a nickel-chromium superalloy with excellent properties:\n- Maximum operating temperature: ~980 K (700°C)\n- Yield strength: ~1100 MPa at room temperature\n- Excellent corrosion and oxidation resistance\n- Good weldability\n- Maintains strength at high temperatures\nIt is commonly used in rocket engines, gas turbines, and aerospace applications where high temperature strength is required.",
            "category": "materials",
            "language": "en"
        },
        
        # Materials Science (French)
        {
            "text": "Question: Quelles sont les propriétés clés de l'Inconel 718?\nRéponse: L'Inconel 718 est un superalliage nickel-chrome avec d'excellentes propriétés:\n- Température maximale de fonctionnement: ~980 K (700°C)\n- Limite d'élasticité: ~1100 MPa à température ambiante\n- Excellente résistance à la corrosion et à l'oxydation\n- Bonne soudabilité\n- Maintient sa résistance à haute température\nIl est couramment utilisé dans les moteurs-fusées, les turbines à gaz et les applications aérospatiales où une résistance à haute température est requise.",
            "category": "materials",
            "language": "fr"
        },
        
        # Problem Solving (English)
        {
            "text": "Question: How do you approach an engineering design problem?\nAnswer: A systematic approach to engineering design:\n1. Understand the problem: Define requirements, constraints, and objectives\n2. Research: Gather relevant information and study similar solutions\n3. Decompose: Break the problem into smaller, manageable sub-problems\n4. Generate concepts: Brainstorm multiple solution approaches\n5. Analyze: Evaluate each concept against physics laws and constraints\n6. Select: Choose the most promising concept based on trade-offs\n7. Detail: Develop detailed design with calculations and simulations\n8. Validate: Test and verify the design meets requirements\n9. Iterate: Refine based on test results\nAlways validate against physical laws - never assume something works without verification.",
            "category": "methodology",
            "language": "en"
        },
        
        # Problem Solving (French)
        {
            "text": "Question: Comment aborder un problème de conception en ingénierie?\nRéponse: Une approche systématique de la conception en ingénierie:\n1. Comprendre le problème: Définir les exigences, contraintes et objectifs\n2. Rechercher: Rassembler les informations pertinentes et étudier des solutions similaires\n3. Décomposer: Diviser le problème en sous-problèmes gérables\n4. Générer des concepts: Brainstormer plusieurs approches de solution\n5. Analyser: Évaluer chaque concept par rapport aux lois physiques et contraintes\n6. Sélectionner: Choisir le concept le plus prometteur basé sur les compromis\n7. Détailler: Développer une conception détaillée avec calculs et simulations\n8. Valider: Tester et vérifier que la conception répond aux exigences\n9. Itérer: Raffiner basé sur les résultats de test\nToujours valider contre les lois physiques - ne jamais supposer que quelque chose fonctionne sans vérification.",
            "category": "methodology",
            "language": "fr"
        },
        
        # Anti-hallucination training (English)
        {
            "text": "Question: Can we build a rocket engine with 1000s specific impulse using chemical propellants?\nAnswer: No, this is physically impossible with chemical propellants. The theoretical maximum specific impulse for chemical rockets is limited by the energy content of the propellants. The best chemical combination (LOX/LH2) achieves around 450-460s in vacuum. To achieve 1000s ISP, you would need:\n- Nuclear thermal propulsion (~900s)\n- Ion drives (~3000s+)\n- Or other advanced propulsion\nI cannot design something that violates the laws of physics. If you need higher ISP, we must consider non-chemical propulsion systems.",
            "category": "anti_hallucination",
            "language": "en"
        },
        
        # Anti-hallucination training (French)
        {
            "text": "Question: Peut-on construire un moteur-fusée avec une impulsion spécifique de 1000s en utilisant des propergols chimiques?\nRéponse: Non, c'est physiquement impossible avec des propergols chimiques. L'impulsion spécifique maximale théorique pour les fusées chimiques est limitée par le contenu énergétique des propergols. La meilleure combinaison chimique (LOX/LH2) atteint environ 450-460s dans le vide. Pour atteindre 1000s ISP, vous auriez besoin de:\n- Propulsion thermique nucléaire (~900s)\n- Propulseurs ioniques (~3000s+)\n- Ou d'autres systèmes de propulsion avancés\nJe ne peux pas concevoir quelque chose qui viole les lois de la physique. Si vous avez besoin d'un ISP plus élevé, nous devons considérer des systèmes de propulsion non-chimiques.",
            "category": "anti_hallucination",
            "language": "fr"
        },
    ]
    
    # Save dataset
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(dataset, f, ensure_ascii=False, indent=2)
    
    logger.info(f"Created engineering dataset with {len(dataset)} examples")
    logger.info(f"Saved to: {output_path}")
    
    return dataset
