#!/usr/bin/env python3
"""
AMA-Intent v2.0 - Aplicación Principal
=======================================
"""

import sys
from pathlib import Path

# Añadir al path
sys.path.insert(0, str(Path(__file__).parent))

def main():
    print("\n" + "="*70)
    print(" AMA-Intent v2.0 - Sistema de Cerebro Artificial Biomimético")
    print("="*70)
    
    # Verificar componentes
    print("\n[VERIFICANDO COMPONENTES]")
    
    try:
        from qodeia_engines import EngineBus
        print("  ✓ Qodeia Engines")
    except ImportError:
        print("  ✗ Qodeia Engines no disponible")
        return
    
    try:
        from ama_phase_integrator import AMAPhaseIntegrator
        print("  ✓ FASE Integration")
        has_fase = True
    except ImportError:
        print("  ⚠️  FASE Integration no disponible (opcional)")
        has_fase = False
    
    # Inicializar sistema
    print("\n[INICIALIZANDO SISTEMA]")
    
    if has_fase:
        ama = AMAPhaseIntegrator()
        print(f"  ✓ Sistema inicializado con {len(ama.bus.list_engines())} motores")
        
        # Test rápido
        print("\n[TEST RÁPIDO]")
        result = ama.process_full("Hola, esto es una prueba del sistema")
        
        if result['ok']:
            print(f"  ✓ Pipeline ejecutado correctamente")
            print(f"  ✓ Intent: {result['fase1']['intent']}")
            print(f"  ✓ Action: {result['fase2']['action']}")
            print(f"  ✓ Quality: {result['fase3']['quality_score']:.1f}/100")
        else:
            print(f"  ✗ Error: {result.get('error')}")
    else:
        # Fallback: solo bus
        bus = EngineBus()
        print(f"  ✓ Bus básico inicializado")
    
    print("\n" + "="*70)
    print(" Sistema listo. Ver documentación para uso avanzado.")
    print("="*70 + "\n")

if __name__ == "__main__":
    main()
