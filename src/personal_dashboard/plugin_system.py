"""
Sistema de plugins para AMA-Intent Personal Dashboard v2
Autor: Manus IA
Fecha: Enero 2026
"""

import hashlib
import importlib
import inspect
import json
import os
import sys
import zipfile
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

# ==================== ENUMS Y MODELOS ====================


class PluginType(Enum):
    """Tipos de plugins soportados"""

    DEBUG_ASSISTANT = "debug_assistant"
    CONTENT_CREATOR = "content_creator"
    INTEGRATION = "integration"
    ANALYTICS = "analytics"
    UI_ENHANCEMENT = "ui_enhancement"
    UTILITY = "utility"


class PluginStatus(Enum):
    """Estado de un plugin"""

    INSTALLED = "installed"
    ACTIVE = "active"
    DISABLED = "disabled"
    ERROR = "error"
    UPDATING = "updating"


@dataclass
class PluginManifest:
    """Manifiesto/metadatos de un plugin"""

    name: str
    version: str
    author: str
    description: str
    plugin_type: PluginType
    entry_point: str  # module.Class o module.function
    dependencies: List[str]
    min_dashboard_version: str = "2.0.0"
    permissions: List[str] = None
    settings_schema: Dict[str, Any] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PluginManifest":
        """Crea un manifiesto desde un diccionario"""
        if "plugin_type" in data:
            data["plugin_type"] = PluginType(data["plugin_type"])
        return cls(**data)

    def to_dict(self) -> Dict[str, Any]:
        """Convierte a diccionario"""
        data = self.__dict__.copy()
        data["plugin_type"] = self.plugin_type.value
        return data


@dataclass
class PluginInstance:
    """Instancia de un plugin cargado"""

    manifest: PluginManifest
    module: Any
    instance: Any
    status: PluginStatus
    error: Optional[str] = None
    settings: Dict[str, Any] = None

    def execute(self, action: str, *args, **kwargs) -> Any:
        """Ejecuta una acción en el plugin"""
        if hasattr(self.instance, action):
            method = getattr(self.instance, action)
            if callable(method):
                return method(*args, **kwargs)

        # Si no tiene el método, buscar en el módulo
        if hasattr(self.module, action):
            func = getattr(self.module, action)
            if callable(func):
                return func(*args, **kwargs)

        raise AttributeError(
            f"Plugin '{self.manifest.name}' no tiene acción '{action}'"
        )


# ==================== GESTOR DE PLUGINS ====================


class PluginManager:
    """Gestor centralizado de plugins"""

    def __init__(self, plugins_dir: str = None):
        if plugins_dir is None:
            base_dir = Path(__file__).parent.parent.parent
            self.plugins_dir = base_dir / "plugins"
        else:
            self.plugins_dir = Path(plugins_dir)

        self.plugins_dir.mkdir(exist_ok=True, parents=True)

        # Registrar directorio de plugins en sys.path
        if str(self.plugins_dir) not in sys.path:
            sys.path.insert(0, str(self.plugins_dir))

        self.plugins: Dict[str, PluginInstance] = {}
        self.hooks: Dict[str, List[Callable]] = {
            "pre_request": [],
            "post_request": [],
            "error_analysis": [],
            "content_generation": [],
            "ui_render": [],
        }

    def discover_plugins(self) -> List[PluginManifest]:
        """Descubre plugins en el directorio"""
        manifests = []

        for plugin_path in self.plugins_dir.iterdir():
            if plugin_path.is_dir():
                manifest_file = plugin_path / "plugin.json"
                if manifest_file.exists():
                    try:
                        with open(manifest_file, "r", encoding="utf-8") as f:
                            manifest_data = json.load(f)

                        manifest = PluginManifest.from_dict(manifest_data)
                        manifests.append(manifest)
                    except Exception as e:
                        print(
                            f"❌ Error cargando manifiesto de {plugin_path.name}: {e}"
                        )

        return manifests

    def load_plugin(self, manifest: PluginManifest) -> Optional[PluginInstance]:
        """Carga un plugin desde su manifiesto"""
        plugin_id = f"{manifest.author}.{manifest.name}"

        try:
            # Parsear entry point (puede ser module o module.Class)
            if "." in manifest.entry_point:
                module_path, class_name = manifest.entry_point.rsplit(".", 1)
            else:
                module_path = manifest.entry_point
                class_name = None

            # Importar módulo
            module = importlib.import_module(module_path)

            # Instanciar clase si se especificó
            if class_name:
                plugin_class = getattr(module, class_name)
                instance = plugin_class()
            else:
                instance = module

            # Crear instancia del plugin
            plugin_instance = PluginInstance(
                manifest=manifest,
                module=module,
                instance=instance,
                status=PluginStatus.ACTIVE,
                settings={},
            )

            # Registrar hooks si el plugin los define
            if hasattr(instance, "register_hooks"):
                instance.register_hooks(self)

            self.plugins[plugin_id] = plugin_instance
            print(f"✅ Plugin cargado: {manifest.name} v{manifest.version}")

            return plugin_instance

        except Exception as e:
            print(f"❌ Error cargando plugin {manifest.name}: {e}")
            error_instance = PluginInstance(
                manifest=manifest,
                module=None,
                instance=None,
                status=PluginStatus.ERROR,
                error=str(e),
            )
            self.plugins[plugin_id] = error_instance
            return None

    def load_all_plugins(self) -> Dict[str, PluginInstance]:
        """Carga todos los plugins disponibles"""
        manifests = self.discover_plugins()

        for manifest in manifests:
            if manifest.name not in self.plugins:
                self.load_plugin(manifest)

        return self.plugins

    def get_plugin(self, plugin_id: str) -> Optional[PluginInstance]:
        """Obtiene un plugin por su ID"""
        return self.plugins.get(plugin_id)

    def get_plugins_by_type(self, plugin_type: PluginType) -> List[PluginInstance]:
        """Obtiene plugins por tipo"""
        return [
            plugin
            for plugin in self.plugins.values()
            if plugin.manifest.plugin_type == plugin_type
        ]

    def register_hook(self, hook_name: str, callback: Callable):
        """Registra una función en un hook"""
        if hook_name in self.hooks:
            self.hooks[hook_name].append(callback)

    def execute_hook(self, hook_name: str, *args, **kwargs) -> List[Any]:
        """Ejecuta todos los callbacks registrados en un hook"""
        results = []

        if hook_name in self.hooks:
            for callback in self.hooks[hook_name]:
                try:
                    result = callback(*args, **kwargs)
                    if result is not None:
                        results.append(result)
                except Exception as e:
                    print(f"❌ Error en hook {hook_name}: {e}")

        return results

    def install_from_zip(self, zip_path: Path) -> bool:
        """Instala un plugin desde archivo ZIP"""
        try:
            # Extraer ZIP
            extract_dir = self.plugins_dir / zip_path.stem
            with zipfile.ZipFile(zip_path, "r") as zip_ref:
                zip_ref.extractall(extract_dir)

            # Buscar y validar manifest
            manifest_file = extract_dir / "plugin.json"
            if not manifest_file.exists():
                raise FileNotFoundError("No se encontró plugin.json")

            with open(manifest_file, "r", encoding="utf-8") as f:
                manifest_data = json.load(f)

            manifest = PluginManifest.from_dict(manifest_data)

            # Instalar dependencias si existen
            deps_file = extract_dir / "requirements.txt"
            if deps_file.exists():
                print(f"📦 Instalando dependencias para {manifest.name}...")
                os.system(f"pip install -r {deps_file}")

            # Cargar plugin
            self.load_plugin(manifest)

            return True

        except Exception as e:
            print(f"❌ Error instalando plugin: {e}")
            return False

    def create_plugin_template(
        self, plugin_name: str, plugin_type: PluginType, author: str = "Desarrollador"
    ) -> Path:
        """Crea una plantilla para un nuevo plugin"""
        plugin_dir = self.plugins_dir / plugin_name.lower().replace(" ", "_")
        plugin_dir.mkdir(exist_ok=True)

        # Crear manifest
        manifest = {
            "name": plugin_name,
            "version": "1.0.0",
            "author": author,
            "description": f"Plugin {plugin_name} para AMA-Intent Dashboard",
            "plugin_type": plugin_type.value,
            "entry_point": f"{plugin_name.lower()}.main.PluginMain",
            "dependencies": [],
            "min_dashboard_version": "2.0.0",
            "permissions": ["read", "write"],
            "settings_schema": {
                "api_key": {"type": "string", "label": "API Key", "required": False},
                "enabled": {"type": "boolean", "label": "Habilitado", "default": True},
            },
        }

        with open(plugin_dir / "plugin.json", "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=2, ensure_ascii=False)

        # Crear estructura de directorios
        (plugin_dir / plugin_name.lower()).mkdir(exist_ok=True)
        (plugin_dir / "static").mkdir(exist_ok=True)
        (plugin_dir / "templates").mkdir(exist_ok=True)

        # Crear archivo main.py
        main_file = plugin_dir / plugin_name.lower() / "main.py"
        main_content = f'''"""
Plugin: {plugin_name}
Autor: {author}
"""

import json
from typing import Dict, Any

class PluginMain:
    """Clase principal del plugin {plugin_name}"""
    
    def __init__(self):
        self.name = "{plugin_name}"
        self.version = "1.0.0"
        self.settings = {{}}
    
    def register_hooks(self, plugin_manager):
        """Registra hooks en el gestor de plugins"""
        # Ejemplo: plugin_manager.register_hook('error_analysis', self.enhance_error_analysis)
        pass
    
    def on_enable(self):
        """Se ejecuta cuando el plugin se habilita"""
        print(f"✅ Plugin {{self.name}} habilitado")
    
    def on_disable(self):
        """Se ejecuta cuando el plugin se deshabilita"""
        print(f"⚠️ Plugin {{self.name}} deshabilitado")
    
    def get_info(self) -> Dict[str, Any]:
        """Devuelve información del plugin"""
        return {{
            "name": self.name,
            "version": self.version,
            "description": "Plugin de ejemplo"
        }}
    
    # Añadir tus métodos específicos aquí
    def custom_action(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Acción personalizada del plugin"""
        return {{"result": "success", "message": "Acción ejecutada", "data": data}}
'''

        with open(main_file, "w", encoding="utf-8") as f:
            f.write(main_content)

        # Crear README
        readme_content = f"""# {plugin_name}

Plugin para AMA-Intent Personal Dashboard v2.

## Características
- [ ] Característica 1
- [ ] Característica 2

## Instalación
1. Copiar esta carpeta al directorio `plugins/`
2. Reiniciar el dashboard
3. Habilitar el plugin desde la interfaz

## Configuración
Editar `plugin.json` para ajustar configuraciones.

## Desarrollo
Implementar métodos en `{plugin_name.lower()}/main.py`
"""

        with open(plugin_dir / "README.md", "w", encoding="utf-8") as f:
            f.write(readme_content)

        print(f"✅ Plantilla creada en: {plugin_dir}")
        return plugin_dir


# ==================== API PARA PLUGINS ====================


class PluginAPI:
    """API que se expone a los plugins"""

    def __init__(self, db_session=None, current_user=None):
        self.db = db_session
        self.user = current_user
        self.available_services = {
            "debug": self.debug_service,
            "content": self.content_service,
            "projects": self.projects_service,
            "analytics": self.analytics_service,
        }

    def debug_service(self, action: str, **kwargs):
        """Servicio de debugging para plugins"""
        from src.code_companion.debug_assistant import DebugAssistant

        assistant = DebugAssistant()

        if action == "analyze":
            return assistant.analyze_error(
                kwargs.get("traceback", ""),
                kwargs.get("code", ""),
                kwargs.get("language", "python"),
            )

        raise ValueError(f"Acción no soportada: {action}")

    def content_service(self, action: str, **kwargs):
        """Servicio de contenido para plugins"""
        from src.content_creator.blog_writer import BlogWriter

        if action == "generate_blog":
            writer = BlogWriter()
            return writer.generate_draft(
                kwargs.get("topic", ""), style=kwargs.get("style", "tutorial")
            )

        raise ValueError(f"Acción no soportada: {action}")

    def projects_service(self, action: str, **kwargs):
        """Servicio de proyectos para plugins"""
        if action == "list":
            # Implementar listado de proyectos desde DB
            return []

        raise ValueError(f"Acción no soportada: {action}")

    def analytics_service(self, action: str, **kwargs):
        """Servicio de analytics para plugins"""
        from .analytics import AnalyticsCalculator

        if action == "get_stats" and self.user:
            calculator = AnalyticsCalculator(self.db, self.user.id)
            return {
                "time_saved": calculator.get_time_saved_total(),
                "code_quality": calculator.get_code_quality_score(),
            }

        raise ValueError(f"Acción no soportada: {action}")

    def call_service(self, service_name: str, action: str, **kwargs):
        """Llama a un servicio del dashboard"""
        if service_name in self.available_services:
            return self.available_services[service_name](action, **kwargs)

        raise ValueError(f"Servicio no disponible: {service_name}")


# ==================== INTEGRACIÓN CON FASTAPI ====================

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

router = APIRouter(prefix="/api/plugins", tags=["plugins"])

# Instancia global del gestor de plugins
plugin_manager = PluginManager()


@router.on_event("startup")
async def startup_plugins():
    """Carga todos los plugins al iniciar"""
    plugin_manager.load_all_plugins()
    print(f"✅ {len(plugin_manager.plugins)} plugins cargados")


@router.get("/")
async def list_plugins():
    """Lista todos los plugins instalados"""
    plugins_list = []

    for plugin_id, plugin in plugin_manager.plugins.items():
        plugins_list.append(
            {
                "id": plugin_id,
                "name": plugin.manifest.name,
                "version": plugin.manifest.version,
                "author": plugin.manifest.author,
                "description": plugin.manifest.description,
                "type": plugin.manifest.plugin_type.value,
                "status": plugin.status.value,
                "error": plugin.error,
            }
        )

    return {"plugins": plugins_list, "total": len(plugins_list)}


@router.get("/types")
async def get_plugin_types():
    """Obtiene los tipos de plugins disponibles"""
    return [
        {"value": pt.value, "label": pt.name.replace("_", " ").title()}
        for pt in PluginType
    ]


@router.get("/{plugin_id}")
async def get_plugin_details(plugin_id: str):
    """Obtiene detalles de un plugin específico"""
    plugin = plugin_manager.get_plugin(plugin_id)

    if not plugin:
        raise HTTPException(status_code=404, detail="Plugin no encontrado")

    return {
        "plugin": {
            "id": plugin_id,
            "manifest": plugin.manifest.to_dict(),
            "status": plugin.status.value,
            "error": plugin.error,
            "settings": plugin.settings,
        }
    }


@router.post("/install")
async def install_plugin(file: UploadFile = File(...)):
    """Instala un plugin desde archivo ZIP"""
    # Guardar archivo temporal
    temp_path = Path("/tmp") / file.filename
    with open(temp_path, "wb") as f:
        content = await file.read()
        f.write(content)

    # Instalar
    success = plugin_manager.install_from_zip(temp_path)

    # Limpiar
    temp_path.unlink(missing_ok=True)

    if success:
        return {"message": "Plugin instalado exitosamente"}
    else:
        raise HTTPException(status_code=400, detail="Error instalando plugin")


@router.post("/{plugin_id}/execute")
async def execute_plugin_action(plugin_id: str, action: str, data: Dict[str, Any]):
    """Ejecuta una acción en un plugin"""
    plugin = plugin_manager.get_plugin(plugin_id)

    if not plugin:
        raise HTTPException(status_code=404, detail="Plugin no encontrado")

    if plugin.status != PluginStatus.ACTIVE:
        raise HTTPException(status_code=400, detail="Plugin no está activo")

    try:
        result = plugin.execute(action, **data)
        return {"success": True, "result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/create-template")
async def create_plugin_template(
    name: str, plugin_type: str, author: str = "Desarrollador"
):
    """Crea una plantilla para un nuevo plugin"""
    try:
        plugin_type_enum = PluginType(plugin_type)
        plugin_dir = plugin_manager.create_plugin_template(
            name, plugin_type_enum, author
        )

        return {
            "message": "Plantilla creada exitosamente",
            "path": str(plugin_dir),
            "next_steps": [
                "1. Editar plugin.json para ajustar metadatos",
                "2. Implementar funcionalidad en main.py",
                "3. Probar con: python ama_personal_dashboard.py",
            ],
        }
    except ValueError:
        raise HTTPException(status_code=400, detail="Tipo de plugin inválido")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
