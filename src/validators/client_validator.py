"""
Client validation utilities.

This module provides validation functions for client data,
including CPF/CNPJ format validation and phone number formatting.
"""

import re
from typing import Optional


class ClientValidator:
    """Utility class for client data validation."""
    
    @staticmethod
    def validate_cpf(cpf: str) -> bool:
        """
        Validate CPF format (Brazilian individual tax ID).
        
        Accepts formats: 000.000.000-00 or 00000000000
        
        Args:
            cpf: CPF string to validate
            
        Returns:
            True if format is valid
        """
        if not cpf:
            return False
        
        # Remove non-numeric characters
        cpf_clean = re.sub(r'[^0-9]', '', cpf)
        
        # CPF must have exactly 11 digits
        if len(cpf_clean) != 11:
            return False
        
        # Check if all digits are the same (invalid CPF)
        if cpf_clean == cpf_clean[0] * 11:
            return False
        
        # CPF validation algorithm
        def calculate_digit(cpf_partial: str, weight: int) -> int:
            """Calculate verification digit."""
            total = sum(int(cpf_partial[i]) * (weight - i) for i in range(len(cpf_partial)))
            remainder = total % 11
            return 0 if remainder < 2 else 11 - remainder
        
        # Validate first digit
        first_digit = calculate_digit(cpf_clean[:9], 10)
        if first_digit != int(cpf_clean[9]):
            return False
        
        # Validate second digit
        second_digit = calculate_digit(cpf_clean[:10], 11)
        if second_digit != int(cpf_clean[10]):
            return False
        
        return True
    
    @staticmethod
    def validate_cnpj(cnpj: str) -> bool:
        """
        Validate CNPJ format (Brazilian company tax ID).
        
        Accepts formats: 00.000.000/0000-00 or 00000000000000
        
        Args:
            cnpj: CNPJ string to validate
            
        Returns:
            True if format is valid
        """
        if not cnpj:
            return False
        
        # Remove non-numeric characters
        cnpj_clean = re.sub(r'[^0-9]', '', cnpj)
        
        # CNPJ must have exactly 14 digits
        if len(cnpj_clean) != 14:
            return False
        
        # Check if all digits are the same (invalid CNPJ)
        if cnpj_clean == cnpj_clean[0] * 14:
            return False
        
        # CNPJ validation algorithm
        def calculate_digit(cnpj_partial: str, weights: list) -> int:
            """Calculate verification digit."""
            total = sum(int(cnpj_partial[i]) * weights[i] for i in range(len(cnpj_partial)))
            remainder = total % 11
            return 0 if remainder < 2 else 11 - remainder
        
        # Weights for first digit
        weights_first = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
        first_digit = calculate_digit(cnpj_clean[:12], weights_first)
        if first_digit != int(cnpj_clean[12]):
            return False
        
        # Weights for second digit
        weights_second = [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
        second_digit = calculate_digit(cnpj_clean[:13], weights_second)
        if second_digit != int(cnpj_clean[13]):
            return False
        
        return True
    
    @staticmethod
    def validate_cpf_cnpj(value: str, tipo: str) -> tuple[bool, str]:
        """
        Validate CPF or CNPJ based on client type.
        
        Args:
            value: CPF or CNPJ string
            tipo: Client type ('pessoa' or 'empresa')
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not value or not value.strip():
            return False, "CPF/CNPJ não pode ser vazio"
        
        # Remove formatting
        clean_value = re.sub(r'[^0-9]', '', value)
        
        if tipo == 'pessoa':
            # For pessoa, accept CPF (11 digits)
            if len(clean_value) == 11:
                if ClientValidator.validate_cpf(value):
                    return True, ""
                else:
                    return False, "CPF inválido"
            else:
                return False, "CPF deve ter 11 dígitos"
        
        elif tipo == 'empresa':
            # For empresa, accept CNPJ (14 digits)
            if len(clean_value) == 14:
                if ClientValidator.validate_cnpj(value):
                    return True, ""
                else:
                    return False, "CNPJ inválido"
            else:
                return False, "CNPJ deve ter 14 dígitos"
        
        return False, "Tipo de cliente inválido"
    
    @staticmethod
    def format_cpf(cpf: str) -> str:
        """
        Format CPF to standard format: 000.000.000-00
        
        Args:
            cpf: CPF string (with or without formatting)
            
        Returns:
            Formatted CPF string
        """
        # Remove non-numeric characters
        cpf_clean = re.sub(r'[^0-9]', '', cpf)
        
        if len(cpf_clean) != 11:
            return cpf  # Return as-is if invalid length
        
        return f"{cpf_clean[:3]}.{cpf_clean[3:6]}.{cpf_clean[6:9]}-{cpf_clean[9:]}"
    
    @staticmethod
    def format_cnpj(cnpj: str) -> str:
        """
        Format CNPJ to standard format: 00.000.000/0000-00
        
        Args:
            cnpj: CNPJ string (with or without formatting)
            
        Returns:
            Formatted CNPJ string
        """
        # Remove non-numeric characters
        cnpj_clean = re.sub(r'[^0-9]', '', cnpj)
        
        if len(cnpj_clean) != 14:
            return cnpj  # Return as-is if invalid length
        
        return f"{cnpj_clean[:2]}.{cnpj_clean[2:5]}.{cnpj_clean[5:8]}/{cnpj_clean[8:12]}-{cnpj_clean[12:]}"
    
    @staticmethod
    def format_phone(phone: str) -> str:
        """
        Format Brazilian phone number.
        
        Accepts: (00) 00000-0000 or (00) 0000-0000
        
        Args:
            phone: Phone string (with or without formatting)
            
        Returns:
            Formatted phone string
        """
        if not phone:
            return ""
        
        # Remove non-numeric characters
        phone_clean = re.sub(r'[^0-9]', '', phone)
        
        if len(phone_clean) == 11:
            # Mobile: (00) 00000-0000
            return f"({phone_clean[:2]}) {phone_clean[2:7]}-{phone_clean[7:]}"
        elif len(phone_clean) == 10:
            # Landline: (00) 0000-0000
            return f"({phone_clean[:2]}) {phone_clean[2:6]}-{phone_clean[6:]}"
        else:
            return phone  # Return as-is if invalid length
    
    @staticmethod
    def validate_phone(phone: str) -> bool:
        """
        Validate Brazilian phone number format.
        
        Args:
            phone: Phone string
            
        Returns:
            True if format is valid
        """
        if not phone:
            return True  # Phone is optional
        
        # Remove non-numeric characters
        phone_clean = re.sub(r'[^0-9]', '', phone)
        
        # Valid lengths: 10 (landline) or 11 (mobile)
        return len(phone_clean) in [10, 11]