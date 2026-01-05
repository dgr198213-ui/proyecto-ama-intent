# ollama_brain_interface.py - Integración Ollama/LM Studio + Cerebro
"""
Interfaz completa entre el Cerebro Artificial y motores de IA local.

Soporta:
- Ollama (API local)
- LM Studio (API compatible OpenAI)
- Modelos locales: Gemma 3, Qwen 3, Llama, etc.

Pipeline:
1. Usuario → texto
2. Cerebro → embedding + AMA-Intent
3. Cerebro → AMA-G Fase 1 (intake)
4. Cerebro → Shadow Prompt
5. Ollama/LM Studio → generación
6. Cerebro → AMA-G Fase 3 (validación)
7. Cerebro → consolidación + aprendizaje
8. Usuario ← respuesta certificada
"""

import numpy as np
import requests
import json
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import time

# Importar módulos del cerebro
from brain_complete import CompleteBrain, CompleteBrainConfig
from ama_intent import extract_intent, validate_intent_immutability, Intent

@dataclass
class LLMConfig:
    """Configuración del motor LLM"""
    provider: str = "ollama"  # "ollama" o "lmstudio"
    base_url: str = "http://localhost:11434"  # Ollama default
    model: str = "gemma2:2b"  # Modelo a usar
    temperature: float = 0.7
    max_tokens: int = 2000
    timeout: int = 60

class TextEmbedder:
    """
    Generador de embeddings para texto.
    
    Usa modelo local o simple (TF-IDF/Bag of Words) como fallback.
    """
    
    def __init__(self, dim: int = 384, method: str = "simple"):
        """
        Args:
            dim: dimensión del embedding
            method: "simple" (BoW) o "model" (sentence-transformers)
        """
        self.dim = dim
        self.method = method
        
        # Vocabulario para BoW
        self.vocab = {}
        self.vocab_size = 0
        
        if method == "model":
            try:
                from sentence_transformers import SentenceTransformer
                print("Cargando modelo de embeddings...")
                self.model = SentenceTransformer('all-MiniLM-L6-v2')
                print("✓ Modelo cargado")
            except ImportError:
                print("⚠ sentence-transformers no disponible, usando método simple")
                self.method = "simple"
    
    def embed(self, text: str) -> np.ndarray:
        """
        Genera embedding de texto.
        
        Args:
            text: texto de entrada
        
        Returns:
            embedding: vector de dimensión self.dim
        """
        if self.method == "model" and hasattr(self, 'model'):
            # Usar modelo de sentence-transformers
            embedding = self.model.encode(text)
            
            # Ajustar dimensión si necesario
            if len(embedding) != self.dim:
                if len(embedding) > self.dim:
                    embedding = embedding[:self.dim]
                else:
                    embedding = np.pad(embedding, (0, self.dim - len(embedding)))
            
            return embedding
        
        else:
            # Método simple: Bag of Words con hash
            words = text.lower().split()
            embedding = np.zeros(self.dim)
            
            for i, word in enumerate(words):
                # Hash de palabra a índice
                idx = hash(word) % self.dim
                embedding[idx] += 1.0 / (i + 1)  # Decay por posición
            
            # Normalizar
            norm = np.linalg.norm(embedding)
            if norm > 0:
                embedding = embedding / norm
            
            return embedding

class OllamaInterface:
    """
    Interfaz con Ollama API.
    """
    
    def __init__(self, config: LLMConfig):
        """
        Args:
            config: configuración de conexión
        """
        self.config = config
        self.base_url = config.base_url.rstrip('/')
    
    def generate(self, 
                prompt: str,
                system_prompt: Optional[str] = None) -> Tuple[str, Dict]:
        """
        Genera respuesta con Ollama.
        
        Args:
            prompt: prompt del usuario
            system_prompt: system prompt (opcional)
        
        Returns:
            response: texto generado
            metadata: metadata de la generación
        """
        url = f"{self.base_url}/api/generate"
        
        payload = {
            "model": self.config.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": self.config.temperature,
                "num_predict": self.config.max_tokens
            }
        }
        
        if system_prompt:
            payload["system"] = system_prompt
        
        try:
            response = requests.post(
                url,
                json=payload,
                timeout=self.config.timeout
            )
            response.raise_for_status()
            
            data = response.json()
            
            return data.get('response', ''), {
                'model': data.get('model'),
                'eval_count': data.get('eval_count', 0),
                'eval_duration': data.get('eval_duration', 0),
                'load_duration': data.get('load_duration', 0)
            }
        
        except requests.exceptions.RequestException as e:
            print(f"Error al conectar con Ollama: {e}")
            return "", {'error': str(e)}
    
    def check_connection(self) -> bool:
        """Verifica conexión con Ollama"""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            return response.status_code == 200
        except:
            return False

class LMStudioInterface:
    """
    Interfaz con LM Studio (compatible con OpenAI API).
    """
    
    def __init__(self, config: LLMConfig):
        """
        Args:
            config: configuración de conexión
        """
        self.config = config
        self.base_url = config.base_url.rstrip('/')
    
    def generate(self,
                prompt: str,
                system_prompt: Optional[str] = None) -> Tuple[str, Dict]:
        """
        Genera respuesta con LM Studio.
        
        Args:
            prompt: prompt del usuario
            system_prompt: system prompt (opcional)
        
        Returns:
            response: texto generado
            metadata: metadata de la generación
        """
        url = f"{self.base_url}/v1/chat/completions"
        
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        payload = {
            "model": self.config.model,
            "messages": messages,
            "temperature": self.config.temperature,
            "max_tokens": self.config.max_tokens
        }
        
        try:
            response = requests.post(
                url,
                json=payload,
                timeout=self.config.timeout
            )
            response.raise_for_status()
            
            data = response.json()
            
            content = data['choices'][0]['message']['content']
            
            return content, {
                'model': data.get('model'),
                'usage': data.get('usage', {}),
                'finish_reason': data['choices'][0].get('finish_reason')
            }
        
        except requests.exceptions.RequestException as e:
            print(f"Error al conectar con LM Studio: {e}")
            return "", {'error': str(e)}
    
    def check_connection(self) -> bool:
        """Verifica conexión con LM Studio"""
        try:
            response = requests.get(f"{self.base_url}/v1/models", timeout=5)
            return response.status_code == 200
        except:
            return False

class GovernedLocalLLM:
    """
    Sistema completo: Cerebro + LLM Local.
    
    Integra el cerebro artificial con Ollama/LM Studio para crear
    una IA local gobernada por AMA-G.
    """
    
    def __init__(self,
                 llm_config: Optional[LLMConfig] = None,
                 brain_config: Optional[CompleteBrainConfig] = None):
        """
        Args:
            llm_config: configuración del LLM
            brain_config: configuración del cerebro
        """
        print("="*70)
        print("🧠 INICIALIZANDO IA LOCAL GOBERNADA")
        print("="*70)
        
        self.llm_config = llm_config or LLMConfig()
        
        # Inicializar interfaz LLM
        print(f"\n[1/3] Conectando con {self.llm_config.provider}...")
        if self.llm_config.provider == "ollama":
            self.llm = OllamaInterface(self.llm_config)
        else:
            self.llm = LMStudioInterface(self.llm_config)
        
        # Verificar conexión
        if self.llm.check_connection():
            print(f"✓ Conectado a {self.llm_config.provider}")
            print(f"  URL: {self.llm_config.base_url}")
            print(f"  Modelo: {self.llm_config.model}")
        else:
            print(f"⚠ No se pudo conectar a {self.llm_config.provider}")
            print(f"  Asegúrate de que esté ejecutándose en {self.llm_config.base_url}")
        
        # Inicializar embedder
        print("\n[2/3] Inicializando embedder...")
        self.embedder = TextEmbedder(dim=384, method="simple")
        print("✓ Embedder listo")
        
        # Inicializar cerebro
        print("\n[3/3] Inicializando cerebro artificial...")
        self.brain = CompleteBrain(brain_config)
        
        # Historial de conversación
        self.conversation_history = []
        
        print("\n" + "="*70)
        print("✅ SISTEMA LISTO")
        print("="*70 + "\n")
    
    def chat(self, user_message: str) -> Dict:
        """
        Procesa un mensaje del usuario con gobernanza completa.
        
        Pipeline completo:
        1. Extraer intención I₀
        2. Generar embedding
        3. Cerebro: intake evaluation (AMA-G Fase 1)
        4. Construir shadow prompt
        5. LLM: generar respuesta
        6. Cerebro: output validation (AMA-G Fase 3)
        7. Consolidación y aprendizaje
        
        Args:
            user_message: mensaje del usuario
        
        Returns:
            Dict con respuesta y metadata
        """
        print(f"\n{'='*70}")
        print(f"💬 Nuevo mensaje: {user_message[:50]}...")
        print(f"{'='*70}\n")
        
        start_time = time.time()
        
        # ==========================================
        # 1. EXTRACCIÓN DE INTENCIÓN (AMA-Intent)
        # ==========================================
        print("[1/7] Extrayendo intención...")
        I0 = extract_intent(user_message)
        
        print(f"  ✓ Intención extraída")
        print(f"    Tipo: {I0.request_type.value}")
        print(f"    Ambigüedad: {I0.ambiguity_score:.2f}")
        print(f"    Complejidad: {I0.complexity_score:.2f}")
        
        # ==========================================
        # 2. EMBEDDING
        # ==========================================
        print("\n[2/7] Generando embedding...")
        embedding = self.embedder.embed(user_message)
        print(f"  ✓ Embedding generado (dim={len(embedding)})")
        
        # ==========================================
        # 3. CEREBRO: INTAKE (Pre-processing)
        # ==========================================
        print("\n[3/7] Evaluación de entrada (AMA-G Fase 1)...")
        
        # Procesar con el cerebro
        brain_result = self.brain.tick(
            observation=embedding,
            reward=None,
            context={
                'user_message': user_message,
                'intent': I0,
                'tags': [I0.request_type.value]
            }
        )
        
        intake_approved = brain_result['execution_mode'] != 'safe_mode'
        
        print(f"  {'✓' if intake_approved else '✗'} Intake: {brain_result['execution_mode']}")
        print(f"    Confianza: {brain_result['metrics']['confidence']:.2f}")
        print(f"    Sorpresa: {brain_result['metrics']['surprise']:.2f}")
        
        if not intake_approved:
            return {
                'response': "Lo siento, no puedo procesar esta solicitud de forma segura.",
                'approved': False,
                'reason': 'intake_failed',
                'brain_state': brain_result
            }
        
        # ==========================================
        # 4. SHADOW PROMPT
        # ==========================================
        print("\n[4/7] Construyendo shadow prompt...")
        
        shadow_prompt = self._build_shadow_prompt(user_message, I0, brain_result)
        
        print(f"  ✓ Shadow prompt construido")
        
        # ==========================================
        # 5. LLM GENERATION
        # ==========================================
        print("\n[5/7] Generando respuesta con LLM...")
        
        llm_response, llm_metadata = self.llm.generate(
            prompt=user_message,
            system_prompt=shadow_prompt
        )
        
        if not llm_response:
            print("  ✗ Error en generación LLM")
            return {
                'response': "Error al generar respuesta.",
                'approved': False,
                'reason': 'llm_error',
                'metadata': llm_metadata
            }
        
        print(f"  ✓ Respuesta generada ({len(llm_response)} chars)")
        
        # ==========================================
        # 6. OUTPUT VALIDATION (AMA-G Fase 3)
        # ==========================================
        print("\n[6/7] Validando respuesta...")
        
        # Generar embedding de la respuesta
        response_embedding = self.embedder.embed(llm_response)
        
        # Extraer intención de la respuesta
        I_response = extract_intent(llm_response)
        
        # Validar inmutabilidad de intención
        intent_preserved = validate_intent_immutability(I0, I_response)
        
        # Procesar respuesta con el cerebro
        validation_result = self.brain.tick(
            observation=response_embedding,
            reward=1.0 if intent_preserved else 0.3,
            context={
                'llm_response': llm_response,
                'intent_preserved': intent_preserved
            }
        )
        
        output_approved = (
            validation_result['execution_mode'] != 'safe_mode' and
            intent_preserved
        )
        
        print(f"  {'✓' if output_approved else '✗'} Validación: {validation_result['execution_mode']}")
        print(f"    Intención preservada: {intent_preserved}")
        print(f"    Confianza: {validation_result['metrics']['confidence']:.2f}")
        
        # ==========================================
        # 7. CONSOLIDACIÓN
        # ==========================================
        print("\n[7/7] Consolidando experiencia...")
        
        # Guardar en historial
        self.conversation_history.append({
            'user': user_message,
            'assistant': llm_response if output_approved else "[BLOQUEADO]",
            'intent': I0,
            'approved': output_approved,
            'brain_state': validation_result
        })
        
        print(f"  ✓ Experiencia consolidada")
        print(f"    Episodios: {validation_result['metrics']['episodes']}")
        print(f"    Conceptos: {validation_result['metrics']['concepts']}")
        
        # ==========================================
        # RESULTADO FINAL
        # ==========================================
        elapsed = time.time() - start_time
        
        print(f"\n{'='*70}")
        print(f"{'✅ RESPUESTA APROBADA' if output_approved else '⚠ RESPUESTA BLOQUEADA'}")
        print(f"Tiempo total: {elapsed:.2f}s")
        print(f"{'='*70}\n")
        
        return {
            'response': llm_response if output_approved else "Respuesta bloqueada por gobernanza.",
            'approved': output_approved,
            'intent_preserved': intent_preserved,
            'brain_state': validation_result,
            'llm_metadata': llm_metadata,
            'elapsed_time': elapsed,
            'original_intent': I0,
            'response_intent': I_response
        }
    
    def _build_shadow_prompt(self,
                            user_message: str,
                            intent: Intent,
                            brain_state: Dict) -> str:
        """
        Construye shadow prompt con contexto de gobernanza.
        
        El shadow prompt NO modifica la solicitud del usuario,
        solo añade restricciones y contexto.
        """
        shadow = f"""Eres un asistente de IA útil y preciso.

CONTEXTO DE GOBERNANZA:
- Tipo de solicitud: {intent.request_type.value}
- Nivel de ambigüedad detectado: {intent.ambiguity_score:.2f}
- Nivel de complejidad: {intent.complexity_score:.2f}
- Confianza del sistema: {brain_state['metrics']['confidence']:.2f}

RESTRICCIONES:
1. Responde SOLO a lo que el usuario pregunta explícitamente
2. NO inventes información que no está en el prompt
3. Si no tienes suficiente información, pídela
4. Mantén la respuesta alineada con el tipo de solicitud: {intent.request_type.value}
5. Si detectas algo ambiguo, pide aclaración

OBJETIVO CENTRAL: {intent.core_goal}

Responde de forma clara, precisa y útil."""
        
        return shadow
    
    def get_statistics(self) -> Dict:
        """Retorna estadísticas completas del sistema"""
        return {
            'total_conversations': len(self.conversation_history),
            'approval_rate': np.mean([c['approved'] for c in self.conversation_history]) if self.conversation_history else 0.0,
            'brain_stats': self.brain.get_complete_statistics()
        }


# =========================
# Testing / Demo
# =========================

if __name__ == "__main__":
    print("\n" + "="*70)
    print("🚀 DEMO: IA LOCAL GOBERNADA")
    print("   Cerebro Artificial + Ollama/LM Studio")
    print("="*70 + "\n")
    
    # Configurar
    llm_config = LLMConfig(
        provider="ollama",  # o "lmstudio"
        base_url="http://localhost:11434",
        model="gemma2:2b",  # Cambia según tu modelo instalado
        temperature=0.7
    )
    
    brain_config = CompleteBrainConfig(
        dim_observation=384,
        dim_latent=64,
        dim_action=16,
        enable_learning=True,
        enable_homeostasis=True
    )
    
    # Inicializar sistema
    governed_llm = GovernedLocalLLM(llm_config, brain_config)
    
    # Conversación de prueba
    test_messages = [
        "Explícame qué es la inteligencia artificial",
        "¿Cuáles son las aplicaciones prácticas de IA?",
        "Escribe código para sumar dos números en Python"
    ]
    
    for msg in test_messages:
        result = governed_llm.chat(msg)
        
        if result['approved']:
            print(f"\n📤 Respuesta:\n{result['response']}\n")
        else:
            print(f"\n⛔ Respuesta bloqueada: {result.get('reason')}\n")
        
        print("-" * 70)
    
    # Estadísticas finales
    print("\n" + "="*70)
    print("📊 ESTADÍSTICAS DEL SISTEMA")
    print("="*70 + "\n")
    
    stats = governed_llm.get_statistics()
    print(f"Conversaciones totales: {stats['total_conversations']}")
    print(f"Tasa de aprobación: {stats['approval_rate']:.1%}")
    print(f"Ticks del cerebro: {stats['brain_stats']['total_ticks']}")
    
    print("\n" + "="*70)
    print("✅ DEMO COMPLETADA")
    print("="*70)