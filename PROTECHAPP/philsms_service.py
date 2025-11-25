"""
PhilSMS Service for sending SMS notifications
API Documentation: https://dashboard.philsms.com/api/v3/
"""
import requests
from django.conf import settings


class PhilSMSService:
    """Service class for sending SMS via PhilSMS API"""
    
    def __init__(self):
        self.api_url = "https://dashboard.philsms.com/api/v3/sms/send"
        self.api_token = getattr(settings, 'PHILSMS_API_TOKEN', '')
    
    def send_sms(self, recipient_number, message, sender_id=None):
        """
        Send SMS to a recipient
        
        Args:
            recipient_number (str): Phone number in format 639XXXXXXXXX or +639XXXXXXXXX
            message (str): SMS message content
            sender_id (str, optional): Sender ID/Name (if configured in PhilSMS)
        
        Returns:
            dict: Response with 'success' boolean and 'message' or 'error'
        """
        if not self.api_token:
            return {
                'success': False,
                'error': 'PhilSMS API token not configured'
            }
        
        # Clean and format phone number
        phone = self._format_phone_number(recipient_number)
        if not phone:
            return {
                'success': False,
                'error': f'Invalid phone number format: {recipient_number}'
            }
        
        # Prepare request payload
        payload = {
            'recipient': phone,
            'message': message,
        }
        
        # Add sender_id only if provided and not None/empty
        if sender_id and str(sender_id).strip():
            payload['sender_id'] = str(sender_id).strip()
        
        # Set headers
        headers = {
            'Authorization': f'Bearer {self.api_token}',
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        
        try:
            # Send POST request
            response = requests.post(
                self.api_url,
                json=payload,
                headers=headers,
                timeout=10
            )
            
            # Check response
            if response.status_code == 200 or response.status_code == 201:
                response_data = response.json()
                return {
                    'success': True,
                    'message': 'SMS sent successfully',
                    'data': response_data
                }
            else:
                error_msg = f'SMS send failed with status {response.status_code}'
                try:
                    error_data = response.json()
                    error_msg = error_data.get('message', error_msg)
                except:
                    error_msg = response.text or error_msg
                
                return {
                    'success': False,
                    'error': error_msg,
                    'status_code': response.status_code
                }
        
        except requests.exceptions.Timeout:
            return {
                'success': False,
                'error': 'SMS request timeout'
            }
        except requests.exceptions.RequestException as e:
            return {
                'success': False,
                'error': f'SMS request failed: {str(e)}'
            }
        except Exception as e:
            return {
                'success': False,
                'error': f'Unexpected error: {str(e)}'
            }
    
    def _format_phone_number(self, phone):
        """
        Format phone number to Philippine format (639XXXXXXXXX)
        
        Args:
            phone (str): Phone number in various formats
        
        Returns:
            str: Formatted phone number or None if invalid
        """
        if not phone:
            return None
        
        # Remove all non-digit characters
        digits = ''.join(filter(str.isdigit, phone))
        
        # Handle different formats
        if digits.startswith('639') and len(digits) == 12:
            # Already in correct format: 639XXXXXXXXX
            return digits
        elif digits.startswith('09') and len(digits) == 11:
            # Convert 09XXXXXXXXX to 639XXXXXXXXX
            return '63' + digits[1:]
        elif digits.startswith('9') and len(digits) == 10:
            # Convert 9XXXXXXXXX to 639XXXXXXXXX
            return '63' + digits
        elif digits.startswith('63') and len(digits) == 11:
            # Missing one digit, might be 63XXXXXXXXX instead of 639XXXXXXXXX
            # This is likely invalid
            return None
        
        # Invalid format
        return None
    
    def send_bulk_sms(self, recipients, message, sender_id=None):
        """
        Send SMS to multiple recipients
        
        Args:
            recipients (list): List of phone numbers
            message (str): SMS message content
            sender_id (str, optional): Sender ID/Name
        
        Returns:
            dict: Results with success/failure counts and details
        """
        results = {
            'total': len(recipients),
            'success': 0,
            'failed': 0,
            'details': []
        }
        
        for recipient in recipients:
            result = self.send_sms(recipient, message, sender_id)
            
            if result['success']:
                results['success'] += 1
            else:
                results['failed'] += 1
            
            results['details'].append({
                'recipient': recipient,
                'result': result
            })
        
        return results


# Convenience function for quick SMS sending
def send_sms(phone_number, message, sender_id=None):
    """
    Quick function to send SMS
    
    Args:
        phone_number (str): Recipient phone number
        message (str): SMS message
        sender_id (str, optional): Sender ID
    
    Returns:
        dict: Response with success status
    """
    service = PhilSMSService()
    return service.send_sms(phone_number, message, sender_id)
