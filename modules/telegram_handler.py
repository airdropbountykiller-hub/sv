#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SV - Telegram Handler Module
Telegram message sending system for Content Creation Engine
"""

import os
import json
import requests
import time
from typing import Dict, List, Optional, Any
from datetime import datetime
import logging
from pathlib import Path

# For proper emoji handling
try:
    # First try our custom module (preferred)
    from sv_emoji import EMOJI, render_emoji
    EMOJI_MODULE = 'sv_emoji'
    print("[OK] SV Emoji module loaded for proper Windows support")
except ImportError:
    # Fall back to emoji package if installed
    try:
        import emoji
        EMOJI_MODULE = 'emoji'
        print("[OK] External emoji module loaded for Windows support")
    except ImportError:
        EMOJI_MODULE = None
        print("[WARN] No emoji module available - emoji may be corrupted on Windows")

# Setup logging
logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

def load_private_config(config_file: str = 'config/private.txt') -> Dict[str, str]:
    """
    Carica configurazione privata da file di testo
    
    Args:
        config_file: Nome del file di configurazione
    
    Returns:
        Dict con configurazioni caricate
    """
    config = {}
    
    # Cerca il file nella directory del progetto
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    config_path = os.path.join(project_root, config_file)
    
    try:
        if os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    # Ignora commenti e righe vuote
                    if line and not line.startswith('#'):
                        if '=' in line:
                            key, value = line.split('=', 1)
                            config[key.strip()] = value.strip()
            
            log.info(f"[OK] [CONFIG] Loaded private config from {config_file}")
        else:
            log.warning(f"[WARN] [CONFIG] Private config file not found: {config_path}")
            log.warning(f"[WARN] [CONFIG] Using default placeholder values")
    
    except Exception as e:
        log.error(f"[ERR] [CONFIG] Error loading private config: {e}")
    
    return config

class TelegramHandler:
    def __init__(self, bot_token: str = None, chat_id: str = None):
        """
        Inizializza handler Telegram
        
        Args:
            bot_token: Token del bot Telegram
            chat_id: ID della chat di destinazione
        """
        # Carica configurazione privata
        private_config = load_private_config()
        
        # Configurazione da parametri, private.txt, o environment variables
        self.bot_token = (
            bot_token or 
            private_config.get('TELEGRAM_BOT_TOKEN') or 
            self._get_config_value('TELEGRAM_BOT_TOKEN', 'YOUR_BOT_TOKEN_HERE')
        )
        self.chat_id = (
            chat_id or 
            private_config.get('TELEGRAM_CHAT_ID') or 
            self._get_config_value('TELEGRAM_CHAT_ID', 'YOUR_CHAT_ID_HERE')
        )
        
        # Base URL API Telegram
        self.base_url = f"https://api.telegram.org/bot{self.bot_token}"
        
        # Configurazione SV-specifica
        self.sv_config = {
            'max_message_length': 4096,  # Limite Telegram
            'retry_attempts': 3,
            'retry_delay': 5,  # secondi
            'enable_preview': False,  # Disabilita preview link per default
'parse_mode': 'HTML',  # Enable HTML formatting for bold/italic
            'timeout': 10  # timeout richieste
        }
        
        # Text-based tags to avoid emoji problems
        self.content_emojis = {
            'press_review': '[PR]',
            'morning': '[AM]', 
            'noon': '[NOON]',
            'evening': '[PM]',
            'summary': '[SUM]',
            'weekly': '[WEEKLY]',
            'monthly': '[MONTHLY]',
            'quarterly': '[QUARTERLY]',
            'semiannual': '[SEMI]',
            'annual': '[ANNUAL]',
            'document': '[DOC]',
            'error': '[ERR]',
            'success': '[OK]',
            'warning': '[WARN]'
        }
        
        # Setup message history for ML analysis and coherence
        project_root = Path(__file__).parent.parent
        self.message_history_dir = project_root / 'reports' / '9_telegram_history'
        self.message_history_dir.mkdir(parents=True, exist_ok=True)
    
    def _get_config_value(self, env_var: str, default: str) -> str:
        """Ottieni valore da environment variable o usa default"""
        return os.environ.get(env_var, default)
    
    def _sanitize_text(self, text) -> str:
        """Robust cleaning for Telegram delivery.
        - Normalize Unicode (NFKC)
        - Strip Private Use Area (BMP and supplementary) and zero-width/control chars
        - Light markdown cleanup (keep emoji)
        """
        if not text:
            return ''
            
        # Convert to string if not already
        if isinstance(text, list):
            text = '\n'.join(str(item) for item in text)
        elif not isinstance(text, str):
            text = str(text)

        # Unicode normalization
        try:
            import unicodedata
            text = unicodedata.normalize('NFKC', text)
        except Exception:
            pass
        
        # Emoji normalization for Windows
        if EMOJI_MODULE == 'sv_emoji':
            # Our custom module has all emoji pre-defined with proper Unicode
            pass
        elif EMOJI_MODULE == 'emoji':
            try:
                import emoji as _emoji
                demojized = _emoji.demojize(text)
                text = _emoji.emojize(demojized)
            except Exception:
                pass  # Continue with original text if emoji processing fails
        
        # Strip Private Use Area characters (BMP U+E000–U+F8FF)
        text = ''.join(ch for ch in text if not (0xE000 <= ord(ch) <= 0xF8FF))
        # Strip Supplementary Private Use Area-A/B (U+F0000–U+FFFFD, U+100000–U+10FFFD)
        text = ''.join(ch for ch in text if not (0xF0000 <= ord(ch) <= 0x10FFFD and (ord(ch) <= 0xFFFFD or ord(ch) >= 0x100000)))
        
        # Remove zero-width and formatting controls
        ZW_CHARS = {
            '\u200B',  # ZERO WIDTH SPACE
            '\u200C',  # ZERO WIDTH NON-JOINER
            '\u200D',  # ZERO WIDTH JOINER
            '\u200E',  # LEFT-TO-RIGHT MARK
            '\u200F',  # RIGHT-TO-LEFT MARK
            '\u2060',  # WORD JOINER
            '\uFEFF',  # ZERO WIDTH NO-BREAK SPACE
        }
        text = ''.join(ch for ch in text if ch not in ZW_CHARS)
        
        # Remove other non-printable control characters (keep newline and tab)
        try:
            text = ''.join(ch for ch in text if ch in ('\n', '\t') or (31 < ord(ch) < 0x110000 and (not unicodedata.category(ch).startswith('C'))))
        except Exception:
            pass
        
        # Light cleanup (do not strip asterisks — used for markup conversion)
        clean_text = text.replace('```', '`')
        
        return clean_text.strip()

    def _format_sv_message(self, content_type: str, content: str, metadata: Dict = None) -> str:
        """
        Format message for Telegram delivery. If the content already contains an SV header,
        avoid adding an extra bot header to prevent duplication and artifacts.
        Applies HTML formatting for bold/italic converted from * and ** markers.
        """
        timestamp = datetime.now().strftime('%H:%M')

        # Light sanitization first (used both for detection and final build)
        safe_content = self._sanitize_text(content)

        # Detect if content already has its own SV header within the first lines
        has_own_header = ('SV - ' in safe_content[:200])

        safe_header = ''
        if not has_own_header:
            emoji = self.content_emojis.get(content_type, '[SV]')
            content_display = {
                'press_review': 'Press Review',
                'morning': 'Morning Report', 
                'noon': 'Noon Update',
                'evening': 'Evening Analysis',
                'summary': 'Daily Summary',
                'weekly': 'Weekly Report',
                'monthly': 'Monthly Report',
                'quarterly': 'Quarterly Report',
                'semiannual': 'Semiannual Report',
                'annual': 'Annual Report',
                'document': 'Document',
                'generic': content_type.title()
            }.get(content_type, content_type.title())

            header = f"{emoji} SV - {content_display} [{timestamp}]\n"
            if metadata:
                if 'market_status' in metadata:
                    header += f"Market: {metadata['market_status']}\n"
                if 'day_context' in metadata:
                    header += f"Context: {metadata['day_context']}\n"
            header += "-" * 35 + "\n\n"
            safe_header = self._sanitize_text(header)

        # Convert simple markdown-style markers to HTML (<b>, <i>) and escape safely
        def _to_html(text: str) -> str:
            import re, html
            # Convert bold (**...**)
            text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)
            # Convert italic (*...*) avoiding double-asterisk cases
            text = re.sub(r"(?<!\*)\*(?!\*)(.+?)\*(?!\*)", r"<i>\1</i>", text)
            # Escape everything, then allow our minimal HTML tags
            escaped = html.escape(text)
            for tag in ["b", "i"]:
                escaped = escaped.replace(f"&lt;{tag}&gt;", f"<{tag}>")
                escaped = escaped.replace(f"&lt;/{tag}&gt;", f"</{tag}>")
            return escaped

        full_message = (_to_html(safe_header) + _to_html(safe_content)).strip()
        
        # Verifica lunghezza e tronca se necessario
        if len(full_message) > self.sv_config['max_message_length']:
            max_content_length = self.sv_config['max_message_length'] - len(safe_header) - 50
            truncated_content = safe_content[:max_content_length] + "\n\n[message truncated - continues...]"
            full_message = safe_header + truncated_content
        
        return full_message
    
    def save_message_for_analysis(self, content: str, content_type: str, 
                                 metadata: Dict = None, telegram_result: Dict = None):
        """Save sent message for ML analysis and coherence tracking"""
        try:
            now = datetime.now()
            date_str = now.strftime('%Y-%m-%d')
            time_str = now.strftime('%H%M%S')
            
            # Create filename: YYYY-MM-DD_HHMMSS_content-type.json
            filename = f"{date_str}_{time_str}_{content_type}.json"
            filepath = self.message_history_dir / filename
            
            # Prepare message data for ML analysis
            message_data = {
                'timestamp': now.isoformat(),
                'date': date_str,
                'time': time_str,
                'content_type': content_type,
                'original_content': content,
                'message_length': len(content),
                'word_count': len(content.split()),
                'metadata': metadata or {},
                'telegram_result': telegram_result or {},
                'sequence_number': self._get_daily_sequence_number(date_str, content_type),
                'ml_features': self._extract_ml_features(content, content_type)
            }
            
            # Save to JSON
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(message_data, f, ensure_ascii=False, indent=2)
            
            log.info(f"[SAVE] [HISTORY] {content_type} message saved for ML analysis: {filename}")
            return str(filepath)
            
        except Exception as e:
            log.error(f"[ERR] [HISTORY] Error saving message history: {e}")
            return None
    
    def _get_daily_sequence_number(self, date_str: str, content_type: str) -> int:
        """Get sequence number for this content type today (for coherence analysis)"""
        try:
            # Count existing files for this content type today
            pattern = f"{date_str}_*_{content_type}.json"
            existing_files = list(self.message_history_dir.glob(pattern))
            return len(existing_files) + 1
        except Exception:
            return 1
    
    def _extract_ml_features(self, content: str, content_type: str) -> Dict:
        """Extract ML features from message content"""
        features = {
            'sentiment_indicators': self._count_sentiment_words(content),
            'prediction_keywords': self._count_prediction_keywords(content),
            'market_terms': self._count_market_terms(content),
            'confidence_level': self._estimate_confidence_level(content),
            'coherence_score': 0.0  # Will be calculated by comparing to previous messages
        }
        
        # Content-type specific features
        if content_type == 'press_review':
            features['sections_count'] = content.count('•')  # Bullet points
            features['news_references'] = content.lower().count('news') + content.lower().count('market')
        elif content_type in ['morning', 'noon', 'evening']:
            features['prediction_count'] = content.count('%') + content.count('target') + content.count('level')
            features['ml_references'] = content.lower().count('ml') + content.lower().count('model')
        
        return features
    
    def _count_sentiment_words(self, text: str) -> Dict[str, int]:
        """Count sentiment indicator words"""
        text_lower = text.lower()
        return {
            'bullish': text_lower.count('bullish') + text_lower.count('positive') + text_lower.count('strong'),
            'bearish': text_lower.count('bearish') + text_lower.count('negative') + text_lower.count('weak'),
            'neutral': text_lower.count('neutral') + text_lower.count('stable') + text_lower.count('balanced')
        }
    
    def _count_prediction_keywords(self, text: str) -> int:
        """Count prediction-related keywords"""
        keywords = ['prediction', 'forecast', 'expect', 'likely', 'target', 'resistance', 'support']
        return sum(text.lower().count(keyword) for keyword in keywords)
    
    def _count_market_terms(self, text: str) -> int:
        """Count market-specific terms"""
        terms = ['s&p', 'nasdaq', 'bitcoin', 'btc', 'eur/usd', 'gold', 'vix', 'fed', 'ecb']
        return sum(text.lower().count(term) for term in terms)
    
    def _estimate_confidence_level(self, text: str) -> float:
        """Estimate confidence level from text indicators"""
        confidence_indicators = {
            'high': ['certain', 'confident', 'strong', 'clear', 'definite'],
            'medium': ['likely', 'probable', 'expect', 'should', 'normal'],
            'low': ['uncertain', 'unclear', 'mixed', 'volatile', 'unpredictable']
        }
        
        text_lower = text.lower()
        high_count = sum(text_lower.count(word) for word in confidence_indicators['high'])
        medium_count = sum(text_lower.count(word) for word in confidence_indicators['medium'])
        low_count = sum(text_lower.count(word) for word in confidence_indicators['low'])
        
        total = high_count + medium_count + low_count
        if total == 0:
            return 0.5  # neutral
        
        return (high_count * 1.0 + medium_count * 0.5 + low_count * 0.0) / total
    
    def send_message(self, content: str, content_type: str = 'generic', 
                    metadata: Dict = None, silent: bool = False) -> Dict:
        """
        Send message Telegram Formatto per SV
        
        Args:
            content: content del message
            content_type: Type content SV
            metadata: Metadati aggiuntivi
            silent: sending silenzioso (senza notifica)
        
        Returns:
            Dict con risultato sending
        """
        try:
            # Format message per SV
            formatted_message = self._format_sv_message(content_type, content, metadata)
            
            # Parametri richiesta
            payload = {
                'chat_id': self.chat_id,
                'text': formatted_message,
                'disable_web_page_preview': not self.sv_config['enable_preview'],
                'disable_notification': silent
            }
            
            # Aggiungi parse_mode solo se specificato
            if self.sv_config['parse_mode']:
                payload['parse_mode'] = self.sv_config['parse_mode']
            
            # Send con retry logic
            for attempt in range(self.sv_config['retry_attempts']):
                try:
                    response = requests.post(
                        f"{self.base_url}/sendMessage",
                        json=payload,
                        timeout=self.sv_config['timeout']
                    )
                    
                    if response.status_code == 200:
                        result = response.json()
                        if result.get('ok'):
                            log.info(f"✅ [TELEGRAM] {content_type} message sent successfully")
                            
                            # Save message for ML analysis and coherence tracking
                            self.save_message_for_analysis(content, content_type, metadata, result)
                            
                            return {
                                'success': True,
                                'message_id': result['result']['message_id'],
                                'content_type': content_type,
                                'timestamp': datetime.now().isoformat()
                            }
                        else:
                            log.error(f"❌ [TELEGRAM] API Error: {result.get('description')}")
                    else:
                        log.error(f"❌ [TELEGRAM] HTTP Error: {response.status_code}")
                
                except requests.exceptions.RequestException as e:
                    log.error(f"❌ [TELEGRAM] Network Error (attempt {attempt + 1}): {e}")
                    
                    if attempt < self.sv_config['retry_attempts'] - 1:
                        time.sleep(self.sv_config['retry_delay'])
                        continue
            
            # Fallimento dopo tutti i tentativi
            return {
                'success': False,
                'error': 'Failed after all retry attempts',
                'content_type': content_type,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            log.error(f"❌ [TELEGRAM] Unexpected error: {e}")
            return {
                'success': False,
                'error': str(e),
                'content_type': content_type,
                'timestamp': datetime.now().isoformat()
            }
    
    def send_sv_content_batch(self, content_list: List[Dict]) -> List[Dict]:
        """
        Send batch di contenuti SV in sequenza
        
        Args:
            content_list: Lista di dict con 'content', 'type', 'metadata'
        
        Returns:
            Lista results sending
        """
        results = []
        
        for i, content_item in enumerate(content_list):
            content = content_item.get('content', '')
            content_type = content_item.get('type') or content_item.get('content_type', 'generic')
            metadata = content_item.get('metadata', {})
            
            # Delay tra messaggi per evitare rate limiting
            if i > 0:
                time.sleep(2)
            
            result = self.send_message(content, content_type, metadata)
            results.append(result)
            
            # Log progress
            if result['success']:
                log.info(f"✅ [BATCH] {i+1}/{len(content_list)} - {content_type} sent")
            else:
                log.error(f"❌ [BATCH] {i+1}/{len(content_list)} - {content_type} failed")
        
        return results
    
    def send_document(self, file_path: str, caption: str = None, 
                     content_type: str = 'document', metadata: Dict = None) -> Dict:
        """
        Send document (PDF, image, etc.) via Telegram
        
        Args:
            file_path: Path to the file to send
            caption: Optional caption for the document
            content_type: Content type for logging (weekly, monthly, etc.)
            metadata: Additional metadata
        
        Returns:
            Dict with sending result
        """
        try:
            import os
            from pathlib import Path
            
            # Check if file exists
            if not os.path.exists(file_path):
                log.error(f"[ERR] [DOCUMENT] File not found: {file_path}")
                return {
                    'success': False,
                    'error': f'File not found: {file_path}',
                    'content_type': content_type
                }
            
            # Get file info
            file_size = os.path.getsize(file_path)
            filename = Path(file_path).name
            
            # Telegram file size limit is 50MB
            if file_size > 50 * 1024 * 1024:  # 50MB
                log.error(f"[ERR] [DOCUMENT] File too large: {file_size} bytes")
                return {
                    'success': False,
                    'error': f'File too large: {file_size} bytes (max 50MB)',
                    'content_type': content_type
                }
            
            # Format caption with SV branding
            if caption:
                emoji = self.content_emojis.get(content_type, '[DOC]')
                timestamp = datetime.now().strftime('%H:%M')
                formatted_caption = f"{emoji} SV - {caption} [{timestamp}]"
            else:
                formatted_caption = None
            
            # Send with retry logic
            for attempt in range(self.sv_config['retry_attempts']):
                try:
                    with open(file_path, 'rb') as doc_file:
                        files = {'document': (filename, doc_file, 'application/pdf')}
                        data = {
                            'chat_id': self.chat_id,
                            'disable_notification': False
                        }
                        
                        if formatted_caption:
                            data['caption'] = formatted_caption
                        
                        response = requests.post(
                            f"{self.base_url}/sendDocument",
                            files=files,
                            data=data,
                            timeout=30  # Longer timeout for file uploads
                        )
                    
                    if response.status_code == 200:
                        result = response.json()
                        if result.get('ok'):
                            log.info(f"✅ [TELEGRAM] {content_type} document sent: {filename} ({file_size} bytes)")
                            
                            # Save for ML analysis
                            doc_metadata = metadata or {}
                            doc_metadata.update({
                                'filename': filename,
                                'file_size': file_size,
                                'file_path': file_path
                            })
                            
                            self.save_message_for_analysis(
                                f"Document sent: {filename}", 
                                content_type, 
                                doc_metadata, 
                                result
                            )
                            
                            return {
                                'success': True,
                                'message_id': result['result']['message_id'],
                                'content_type': content_type,
                                'filename': filename,
                                'file_size': file_size,
                                'timestamp': datetime.now().isoformat()
                            }
                        else:
                            log.error(f"❌ [TELEGRAM] API Error: {result.get('description')}")
                    else:
                        log.error(f"❌ [TELEGRAM] HTTP Error: {response.status_code}")
                
                except requests.exceptions.RequestException as e:
                    log.error(f"❌ [TELEGRAM] Network Error (attempt {attempt + 1}): {e}")
                    
                    if attempt < self.sv_config['retry_attempts'] - 1:
                        time.sleep(self.sv_config['retry_delay'])
                        continue
            
            # Failed after all attempts
            return {
                'success': False,
                'error': 'Failed after all retry attempts',
                'content_type': content_type,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            log.error(f"❌ [TELEGRAM] Document sending error: {e}")
            return {
                'success': False,
                'error': str(e),
                'content_type': content_type,
                'timestamp': datetime.now().isoformat()
            }
    
    def send_daily_summary(self, summary_data: Dict) -> Dict:
        """Send Daily Summary formattato per SV.

        Nota: non è usato dal flusso intraday automatico; è pensato per invii
        manuali/legacy da script esterni o test.

        Args:
            summary_data: Dati del summary con sezioni multiple

        Returns:
            Risultato sending
        """
        try:
            # Costruisci summary Formatto
            content = "**DAILY SUMMARY COMPLETO**\n\n"
            # Sezione performance
            if 'performance' in summary_data:
                perf = summary_data['performance']
                content += f"📊 **performance Overview**\n"
                content += f"• Accuracy: `{perf.get('accuracy', 'N/A')}`\n"
                content += f"• Total Signals: `{perf.get('total_signals', 'N/A')}`\n"
                content += f"• Success Rate: `{perf.get('success_rate', 'N/A')}`\n\n"
            
            # Sezione Market Analysis
            if 'market_analysis' in summary_data:
                analysis = summary_data['market_analysis']
                content += f"🎯 **Market Analysis**\n"
                content += f"• Regime: `{analysis.get('regime', 'TBD')}`\n"
                content += f"• Sentiment: `{analysis.get('sentiment', 'NEUTRAL')}`\n"
                content += f"• Volatility: `{analysis.get('volatility', 'NORMAL')}`\n\n"
            
            # Tomorrow Outlook
            if 'tomorrow_outlook' in summary_data:
                outlook = summary_data['tomorrow_outlook']
                content += f"🔮 **Tomorrow Outlook**\n"
                content += f"{outlook}\n\n"
            
            # Footer
            content += f"📈 *SV Content Engine - Daily Wrap*"
            
            return self.send_message(content, 'summary', summary_data.get('metadata', {}))
            
        except Exception as e:
            log.error(f"❌ [DAILY-SUMMARY] Error: {e}")
            return {'success': False, 'error': str(e)}
    
    def test_connection(self) -> bool:
        """Test connessione Telegram bot"""
        try:
            response = requests.get(f"{self.base_url}/getMe", timeout=5)
            if response.status_code == 200:
                result = response.json()
                if result.get('ok'):
                    bot_info = result['result']
                    log.info(f"✅ [TELEGRAM] Bot connected: {bot_info.get('first_name')} (@{bot_info.get('username')})")
                    return True
            
            log.error("❌ [TELEGRAM] Bot connection failed")
            return False
            
        except Exception as e:
            log.error(f"❌ [TELEGRAM] Connection test error: {e}")
            return False

# Singleton instance per SV
telegram_handler = None

def get_telegram_handler(bot_token: str = None, chat_id: str = None) -> TelegramHandler:
    """Ottieni istanza singleton del Telegram handler"""
    global telegram_handler
    if telegram_handler is None:
        telegram_handler = TelegramHandler(bot_token, chat_id)
    return telegram_handler

def send_sv_message(content: str, content_type: str = 'generic', 
                   metadata: Dict = None) -> Dict:
    """
    Helper function per Sendre messaggi SV rapidamente
    
    Args:
        content: content message
        content_type: Type content (press_review, morning, etc.)
        metadata: Metadati aggiuntivi
    
    Returns:
        Risultato sending
    """
    handler = get_telegram_handler()
    return handler.send_message(content, content_type, metadata)

def send_sv_error(error_message: str, context: str = '') -> Dict:
    """Send message di errore SV.

    Helper legacy/non-critico: non è richiamato dal core engine, ma utile
    per script operativi e test manuali.
    """
    content = f"**ERRORE SISTEMA SV**\n\n"
    if context:
        content += f"Contesto: `{context}`\n"
    content += f"Errore: `{error_message}`\n\n"
    content += f"⚠️ *Verificare sistema e log*"
    
    return send_sv_message(content, 'error')

def send_sv_success(message: str, details: str = '') -> Dict:
    """Send message di successo SV.

    Helper legacy/non-critico: non è richiamato dal core engine, ma utile
    per script operativi e test manuali.
    """
    content = f"**OPERAZIONE COMPLETATA**\n\n"
    content += f"✅ {message}\n"
    if details:
        content += f"\nDettagli: `{details}`"
    
    return send_sv_message(content, 'success')

# Test function
def test_telegram_integration():
    """Test completo integrazione Telegram per SV"""
    print("ðŸ§ª [TEST] Testing Telegram Integration...")
    
    handler = get_telegram_handler()
    
    # Test 1: Connessione
    if not handler.test_connection():
        print("âŒ [TEST] Connection failed")
        return False
    
    # Test 2: message singolo
    test_result = handler.send_message(
        "Test message from SV Content Engine", 
        'morning',
        {'market_status': 'OPEN', 'day_context': 'Tuesday Test'}
    )
    
    if test_result['success']:
        print("âœ… [TEST] Single message sent successfully")
    else:
        print("âŒ [TEST] Single message failed")
        return False
    
    print("âœ… [TEST] Telegram integration working correctly")
    return True

if __name__ == '__main__':
    test_telegram_integration()




