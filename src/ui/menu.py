"""
Terminal menu system.

This module provides the main menu interface for the perfumery management system.
"""

import os
import sys
from typing import Callable, Dict, Optional


class Menu:
    """
    Terminal menu system with navigation and input handling.
    """
    
    def __init__(self, title: str):
        """
        Initialize menu.
        
        Args:
            title: Menu title to display
        """
        self.title = title
        self.options: Dict[str, tuple[str, Callable]] = {}
        self.running = True
    
    def add_option(self, key: str, description: str, handler: Callable):
        """
        Add a menu option.
        
        Args:
            key: Key to press (e.g., '1', 'a')
            description: Description to display
            handler: Function to call when selected
        """
        self.options[key] = (description, handler)
    
    def clear_screen(self):
        """Clear the terminal screen."""
        os.system('cls' if os.name == 'nt' else 'clear')
    
    def print_header(self):
        """Print menu header."""
        width = 70
        print("\n" + "="*width)
        print(f"  {self.title}")
        print("="*width)
    
    def print_options(self):
        """Print menu options."""
        print("\nOpções:")
        for key, (description, _) in sorted(self.options.items()):
            print(f"  [{key}] {description}")
        print()
    
    def get_input(self, prompt: str, allow_empty: bool = False) -> str:
        """
        Get user input with validation.
        
        Args:
            prompt: Prompt to display
            allow_empty: Whether to allow empty input
            
        Returns:
            User input string
        """
        while True:
            try:
                value = input(prompt).strip()
                
                if not value and not allow_empty:
                    print("⚠️  Este campo não pode ser vazio. Tente novamente.")
                    continue
                
                return value
            except (EOFError, KeyboardInterrupt):
                print("\n\n⚠️  Operação cancelada.")
                return ""
    
    def get_number(self, prompt: str, min_value: Optional[float] = None, 
                   max_value: Optional[float] = None, is_float: bool = False) -> Optional[float]:
        """
        Get numeric input with validation.
        
        Args:
            prompt: Prompt to display
            min_value: Minimum allowed value
            max_value: Maximum allowed value
            is_float: Whether to accept decimal numbers
            
        Returns:
            Numeric value or None if cancelled
        """
        while True:
            try:
                value_str = self.get_input(prompt)
                
                if not value_str:
                    return None
                
                # Convert to number
                value = float(value_str) if is_float else int(value_str)
                
                # Validate range
                if min_value is not None and value < min_value:
                    print(f"⚠️  Valor deve ser maior ou igual a {min_value}")
                    continue
                
                if max_value is not None and value > max_value:
                    print(f"⚠️  Valor deve ser menor ou igual a {max_value}")
                    continue
                
                return value
                
            except ValueError:
                tipo = "decimal" if is_float else "inteiro"
                print(f"⚠️  Por favor, digite um número {tipo} válido.")
    
    def confirm(self, message: str, default: bool = False) -> bool:
        """
        Ask for yes/no confirmation.
        
        Args:
            message: Confirmation message
            default: Default value if user just presses Enter
            
        Returns:
            True for yes, False for no
        """
        default_str = "S/n" if default else "s/N"
        response = self.get_input(f"{message} ({default_str}): ", allow_empty=True).lower()
        
        if not response:
            return default
        
        return response in ['s', 'sim', 'y', 'yes']
    
    def pause(self, message: str = "\nPressione ENTER para continuar..."):
        """
        Pause and wait for user input.
        
        Args:
            message: Message to display
        """
        try:
            input(message)
        except (EOFError, KeyboardInterrupt):
            pass
    
    def show_error(self, message: str):
        """
        Display error message.
        
        Args:
            message: Error message
        """
        print(f"\n❌ ERRO: {message}")
    
    def show_success(self, message: str):
        """
        Display success message.
        
        Args:
            message: Success message
        """
        print(f"\n✅ {message}")
    
    def show_warning(self, message: str):
        """
        Display warning message.
        
        Args:
            message: Warning message
        """
        print(f"\n⚠️  {message}")
    
    def show_info(self, message: str):
        """
        Display info message.
        
        Args:
            message: Info message
        """
        print(f"\nℹ️  {message}")
    
    def display(self):
        """Display the menu and handle user input."""
        while self.running:
            try:
                self.clear_screen()
                self.print_header()
                self.print_options()
                
                choice = self.get_input("Escolha uma opção: ", allow_empty=True)
                
                if not choice:
                    continue
                
                if choice in self.options:
                    _, handler = self.options[choice]
                    
                    # Clear screen before running handler
                    self.clear_screen()
                    
                    try:
                        handler()
                    except KeyboardInterrupt:
                        print("\n\n⚠️  Operação cancelada pelo usuário.")
                    except Exception as e:
                        self.show_error(f"Erro inesperado: {str(e)}")
                        import traceback
                        traceback.print_exc()
                    
                    self.pause()
                else:
                    self.show_warning(f"Opção '{choice}' inválida. Tente novamente.")
                    self.pause()
                    
            except KeyboardInterrupt:
                print("\n\nEncerrando o sistema...")
                self.running = False
            except Exception as e:
                self.show_error(f"Erro fatal: {str(e)}")
                import traceback
                traceback.print_exc()
                self.pause()
    
    def exit(self):
        """Exit the menu."""
        self.running = False


def create_submenu(title: str, parent_menu: Optional[Menu] = None) -> Menu:
    """
    Create a submenu with automatic back option.
    
    Args:
        title: Submenu title
        parent_menu: Parent menu to return to
        
    Returns:
        Menu instance
    """
    menu = Menu(title)
    
    if parent_menu is not None:
        menu.add_option('0', '← Voltar', lambda: menu.exit())
    else:
        menu.add_option('0', '← Sair', lambda: menu.exit())
    
    return menu