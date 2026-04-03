"""
Interactive Chat Interface for KÁNU Intelligence
Full R&D department accessible through conversational interface
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from kanu_intelligence.intelligence_orchestrator import create_intelligence_system
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from rich.table import Table
import logging

logging.basicConfig(level=logging.INFO)
console = Console()


class KANUChat:
    """Interactive chat interface for KÁNU Intelligence"""
    
    def __init__(self):
        self.kanu = create_intelligence_system(enable_advanced=True)
        self.session_active = True
        
    def start(self):
        """Start interactive chat session"""
        self._print_welcome()
        
        while self.session_active:
            try:
                user_input = console.input("\n[bold cyan]You:[/bold cyan] ")
                
                if not user_input.strip():
                    continue
                
                # Handle special commands
                if user_input.lower() in ['exit', 'quit', 'bye']:
                    self._handle_exit()
                    break
                
                elif user_input.lower() == 'status':
                    self._show_status()
                    continue
                
                elif user_input.lower() == 'designs':
                    self._show_designs()
                    continue
                
                elif user_input.lower() == 'report':
                    self._export_report()
                    continue
                
                elif user_input.lower() == 'help':
                    self._show_help()
                    continue
                
                # Process through KÁNU Intelligence
                response = self.kanu.chat(user_input)
                
                self._display_response(response)
                
            except KeyboardInterrupt:
                self._handle_exit()
                break
            except Exception as e:
                console.print(f"[red]Error: {e}[/red]")
                logging.exception("Chat error")
    
    def _print_welcome(self):
        """Print welcome message"""
        console.print("\n[bold cyan]═══════════════════════════════════════════════════════════[/bold cyan]")
        console.print("[bold cyan]  KÁNU Intelligence System                                 [/bold cyan]")
        console.print("[bold cyan]  Full R&D Department - Accessible Through Chat            [/bold cyan]")
        console.print("[bold cyan]  'Born from love. Bound by physics.'                      [/bold cyan]")
        console.print("[bold cyan]═══════════════════════════════════════════════════════════[/bold cyan]\n")
        
        console.print("[yellow]I'm your senior rocket engineer. Let's design something amazing together.[/yellow]")
        console.print("[dim]Type 'help' for commands, 'exit' to quit[/dim]\n")
    
    def _display_response(self, response: dict):
        """Display KÁNU's response"""
        # Main message
        console.print(f"\n[bold green]KÁNU:[/bold green] {response['message']}\n")
        
        # Questions
        if response.get('questions'):
            console.print("[bold yellow]Questions:[/bold yellow]")
            for q in response['questions']:
                console.print(f"  • {q}")
            console.print()
        
        # Insights
        if response.get('insights'):
            console.print("[bold cyan]Key Insights:[/bold cyan]")
            for insight in response['insights']:
                console.print(f"  • {insight}")
            console.print()
        
        # Concerns
        if response.get('concerns'):
            console.print("[bold red]Concerns:[/bold red]")
            for concern in response['concerns']:
                console.print(f"  • {concern}")
            console.print()
        
        # Recommendations
        if response.get('recommendations'):
            console.print("[bold green]Recommendations:[/bold green]")
            for rec in response['recommendations']:
                console.print(f"  • {rec}")
            console.print()
        
        # Designs generated
        if response.get('designs'):
            self._display_designs(response['designs'])
        
        # Validation results
        if response.get('validation'):
            self._display_validation(response['validation'])
        
        # Phase indicator
        phase = response.get('phase', 'unknown')
        console.print(f"[dim]Phase: {phase} | Depth: {response.get('technical_depth', 5)}/10[/dim]")
    
    def _display_designs(self, designs_data: dict):
        """Display generated designs"""
        console.print("\n[bold cyan]═══ Design Proposals ═══[/bold cyan]\n")
        
        proposals = designs_data.get('proposals', [])
        
        for i, proposal in enumerate(proposals, 1):
            panel_content = (
                f"[cyan]Propellant:[/cyan] {proposal['key_parameters']['propellant']}\n"
                f"[cyan]Chamber Pressure:[/cyan] {proposal['key_parameters']['chamber_pressure_mpa']:.1f} MPa\n"
                f"[cyan]Expansion Ratio:[/cyan] {proposal['key_parameters']['expansion_ratio']:.0f}\n\n"
                f"[green]Predicted ISP:[/green] {proposal['predicted_performance']['isp_s']:.0f} s\n"
                f"[green]Predicted Thrust:[/green] {proposal['predicted_performance']['thrust_kn']:.0f} kN\n\n"
                f"[yellow]Cost Estimate:[/yellow] ${proposal['cost_estimate_usd']/1e6:.2f}M\n"
                f"[yellow]Complexity:[/yellow] {proposal['manufacturing_complexity']}\n"
                f"[yellow]Score:[/yellow] {proposal['overall_score']:.1f}/100\n\n"
                f"[dim]{proposal['rationale'][:150]}...[/dim]"
            )
            
            console.print(Panel(
                panel_content,
                title=f"[bold]{proposal['name']}[/bold]",
                border_style="cyan" if i == 1 else "blue"
            ))
        
        # Comparison
        if designs_data.get('comparison'):
            console.print("\n[bold]Recommendation:[/bold]")
            console.print(designs_data.get('recommendation', ''))
    
    def _display_validation(self, validation_data: dict):
        """Display validation results"""
        console.print("\n[bold cyan]═══ Validation Results ═══[/bold cyan]\n")
        
        for result in validation_data.get('validation_results', []):
            fmea = result['fmea_summary']
            console.print(f"[bold]{result['design_name']}[/bold]")
            console.print(f"  Risk Score: {fmea['overall_risk_score']:.1f}/100")
            console.print(f"  Critical Failures: {fmea['critical_failures']}")
            console.print(f"  Top Risks: {', '.join(fmea['top_risks'][:2])}")
            console.print()
    
    def _show_status(self):
        """Show system status"""
        status = self.kanu.get_system_status()
        
        table = Table(title="System Status")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green")
        
        table.add_row("Conversation Phase", status['conversation_phase'])
        table.add_row("Workflow Stage", status['workflow_stage'])
        table.add_row("Designs Generated", str(status['designs_generated']))
        table.add_row("Iterations", str(status['iterations_completed']))
        table.add_row("Conversation Turns", str(status['conversation_turns']))
        
        if 'best_design_score' in status:
            table.add_row("Best Design Score", f"{status['best_design_score']:.1f}/100")
        
        if 'risk_score' in status:
            table.add_row("Risk Score", f"{status['risk_score']:.1f}/100")
        
        console.print(table)
    
    def _show_designs(self):
        """Show current designs"""
        if not self.kanu.current_designs:
            console.print("[yellow]No designs generated yet[/yellow]")
            return
        
        table = Table(title="Current Designs")
        table.add_column("Name", style="cyan")
        table.add_column("Propellant", style="green")
        table.add_column("ISP (s)", justify="right")
        table.add_column("Thrust (kN)", justify="right")
        table.add_column("Score", justify="right")
        
        for design in self.kanu.current_designs:
            table.add_row(
                design.name,
                design.parameters.get('propellant_name', 'N/A'),
                f"{design.predicted_performance.get('isp', 0):.0f}",
                f"{design.predicted_performance.get('thrust', 0)/1000:.0f}",
                f"{design.overall_score:.1f}"
            )
        
        console.print(table)
    
    def _export_report(self):
        """Export engineering report"""
        console.print("\n[yellow]Generating engineering report...[/yellow]")
        
        report = self.kanu.export_engineering_report()
        
        filename = f"kanu_report_{int(time.time())}.md"
        with open(filename, 'w') as f:
            f.write(report)
        
        console.print(f"[green]✓ Report saved to {filename}[/green]")
        
        # Also display summary
        console.print("\n[bold]Report Preview:[/bold]")
        console.print(Markdown(report[:500] + "\n\n[... full report in file ...]"))
    
    def _show_help(self):
        """Show help message"""
        help_text = """
        [bold cyan]KÁNU Intelligence Commands:[/bold cyan]
        
        [bold]Chat Commands:[/bold]
        - Just type naturally to discuss your rocket engine design
        - Ask questions, request designs, provide feedback
        
        [bold]Special Commands:[/bold]
        - [cyan]status[/cyan]  - Show system status
        - [cyan]designs[/cyan] - Show current design proposals
        - [cyan]report[/cyan]  - Export engineering report
        - [cyan]help[/cyan]    - Show this help
        - [cyan]exit[/cyan]    - Exit chat
        
        [bold]Example Conversations:[/bold]
        - "I need a high-efficiency vacuum engine"
        - "Design a booster with LOX/RP-1"
        - "Show me 3 design options"
        - "Refine design 2 to reduce cost"
        - "Run failure analysis"
        """
        console.print(Panel(help_text, title="Help", border_style="cyan"))
    
    def _handle_exit(self):
        """Handle exit"""
        console.print("\n[yellow]Exporting conversation log...[/yellow]")
        
        log = self.kanu.export_conversation_log()
        filename = f"kanu_conversation_{int(time.time())}.md"
        
        with open(filename, 'w') as f:
            f.write(log)
        
        console.print(f"[green]✓ Conversation saved to {filename}[/green]")
        console.print("\n[cyan]Thank you for using KÁNU Intelligence. Happy engineering! 🚀[/cyan]\n")
        
        self.session_active = False


def main():
    """Main entry point"""
    import time
    
    chat = KANUChat()
    chat.start()


if __name__ == "__main__":
    main()
