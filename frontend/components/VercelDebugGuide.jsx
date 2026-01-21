import React, { useState } from 'react';
import { AlertTriangle, CheckCircle, XCircle, Copy, Terminal, FileCode, Settings } from 'lucide-react';

export default function VercelDebugGuide() {
  const [copied, setCopied] = useState('');
  const [activeTab, setActiveTab] = useState('diagnosis');

  const copyCode = (text, id) => {
    navigator.clipboard.writeText(text);
    setCopied(id);
    setTimeout(() => setCopied(''), 2000);
  };

  const CodeBlock = ({ code, id, language = 'bash' }) => (
    <div className="relative bg-gray-900 rounded-lg p-4 mt-2">
      <button
        onClick={() => copyCode(code, id)}
        className="absolute top-2 right-2 p-2 bg-gray-800 rounded hover:bg-gray-700 transition"
      >
        {copied === id ? (
          <CheckCircle size={16} className="text-green-400" />
        ) : (
          <Copy size={16} className="text-gray-400" />
        )}
      </button>
      <pre className="text-sm text-green-300 overflow-x-auto pr-12">
        <code>{code}</code>
      </pre>
    </div>
  );

  const tabs = {
    diagnosis: {
      icon: AlertTriangle,
      title: 'Diagnóstico',
      content: (
        <div className="space-y-4">
          <div className="bg-red-900/20 border border-red-500 rounded-lg p-4">
            <h3 className="text-red-400 font-bold mb-2 flex items-center gap-2">
              <XCircle size={20} />
              Errores Detectados (100% Error Rate)
            </h3>
            <ul className="space-y-2 text-red-200 text-sm">
              <li>• <strong>PYTHONPATH incorrecto</strong> - Los módulos no se encuentran</li>
              <li>• <strong>Dependencias faltantes</strong> - Algunas librerías no instaladas</li>
              <li>• <strong>Variables de entorno</strong> - Claves no configuradas en Vercel</li>
              <li>• <strong>Base de datos SQLite</strong> - No funciona en serverless</li>
            </ul>
          </div>

          <div className="bg-yellow-900/20 border border-yellow-500 rounded-lg p-4">
            <h3 className="text-yellow-400 font-bold mb-2">¿Por qué falla?</h3>
            <p className="text-yellow-200 text-sm mb-2">
              Tu proyecto está diseñado para correr localmente con SQLite, pero Vercel es un 
              entorno <strong>serverless</strong> donde:
            </p>
            <ul className="space-y-1 text-yellow-200 text-sm">
              <li>→ No hay sistema de archivos persistente</li>
              <li>→ Cada request crea un nuevo contenedor</li>
              <li>→ SQLite se borra entre invocaciones</li>
              <li>→ Los paths relativos no funcionan igual</li>
            </ul>
          </div>

          <div className="bg-blue-900/20 border border-blue-500 rounded-lg p-4">
            <h3 className="text-blue-400 font-bold mb-2 flex items-center gap-2">
              <CheckCircle size={20} />
              Solución Inmediata
            </h3>
            <p className="text-blue-200 text-sm">
              Necesitas <strong>migrar a Supabase</strong> (PostgreSQL) ANTES de que Vercel funcione.
              El deployment actual seguirá fallando hasta que hagas este cambio.
            </p>
          </div>
        </div>
      )
    },
    
    fix: {
      icon: Settings,
      title: 'Correcciones',
      content: (
        <div className="space-y-6">
          <div>
            <h3 className="text-white font-bold mb-3 flex items-center gap-2">
              <Terminal size={20} />
              1. Actualizar vercel.json
            </h3>
            <p className="text-gray-300 text-sm mb-2">
              Reemplaza tu vercel.json actual con esta configuración:
            </p>
            <CodeBlock
              id="vercel_json"
              code={`{
  "buildCommand": "pip install -r requirements.txt",
  "functions": {
    "backend/main.py": {
      "runtime": "python3.9",
      "maxDuration": 30
    }
  },
  "routes": [
    {
      "src": "/api/(.*)",
      "dest": "backend/main.py"
    },
    {
      "src": "/(.*)",
      "dest": "frontend/$1"
    }
  ],
  "env": {
    "PYTHONPATH": "/var/task"
  }
}`}
            />
          </div>

          <div>
            <h3 className="text-white font-bold mb-3">2. Actualizar requirements.txt</h3>
            <p className="text-gray-300 text-sm mb-2">
              Asegúrate de tener TODAS estas dependencias:
            </p>
            <CodeBlock
              id="requirements"
              code={`fastapi==0.104.1
uvicorn[standard]==0.24.0
sqlalchemy==2.0.23
psycopg2-binary==2.9.9
python-dotenv==1.0.0
pydantic==2.5.0
pydantic-settings==2.1.0
cryptography==41.0.7
aiohttp==3.9.1
pyyaml==6.0.1
networkx==3.2.1`}
            />
          </div>

          <div>
            <h3 className="text-white font-bold mb-3">3. Configurar Variables de Entorno</h3>
            <p className="text-gray-300 text-sm mb-2">
              En Vercel → Settings → Environment Variables, agrega:
            </p>
            <div className="bg-gray-900 rounded-lg p-4 space-y-2">
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div className="text-gray-400">Variable</div>
                <div className="text-gray-400">Valor</div>
                
                <div className="text-green-300 font-mono">DATABASE_URL</div>
                <div className="text-blue-300 break-all">postgresql://postgres:...</div>
                
                <div className="text-green-300 font-mono">MINIMAX_API_KEY</div>
                <div className="text-blue-300">tu_clave_minimax</div>
                
                <div className="text-green-300 font-mono">MINIMAX_GROUP_ID</div>
                <div className="text-blue-300">tu_grupo_id</div>
                
                <div className="text-green-300 font-mono">CREDENTIAL_MASTER_KEY</div>
                <div className="text-blue-300">tu_master_key</div>
              </div>
            </div>
          </div>

          <div>
            <h3 className="text-white font-bold mb-3">4. Adaptar database.py</h3>
            <p className="text-gray-300 text-sm mb-2">
              Modifica <code className="bg-gray-800 px-2 py-1 rounded">backend/data/database.py</code>:
            </p>
            <CodeBlock
              id="database_py"
              language="python"
              code={`import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# Detectar entorno
DATABASE_URL = os.getenv('DATABASE_URL')

if not DATABASE_URL:
    raise ValueError("DATABASE_URL no configurada")

# Si es PostgreSQL, ajustar URL para SQLAlchemy
if DATABASE_URL.startswith('postgres://'):
    DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql://', 1)

# Crear engine
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,  # Verificar conexión antes de usar
    pool_recycle=3600,   # Reciclar conexiones cada hora
    echo=False
)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()`}
            />
          </div>
        </div>
      )
    },

    migrate: {
      icon: FileCode,
      title: 'Migración a Supabase',
      content: (
        <div className="space-y-6">
          <div className="bg-purple-900/20 border border-purple-500 rounded-lg p-4">
            <h3 className="text-purple-400 font-bold mb-2">⚡ Migración Rápida</h3>
            <p className="text-purple-200 text-sm">
              Este script automatiza todo el proceso de migración:
            </p>
          </div>

          <div>
            <h3 className="text-white font-bold mb-3">Script de Migración Completo</h3>
            <CodeBlock
              id="migrate_script"
              language="python"
              code={`#!/usr/bin/env python3
"""
Script de migración SQLite → Supabase
Ejecutar: python migrate_to_supabase.py
"""
import os
import sqlite3
from sqlalchemy import create_engine, MetaData, Table
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

load_dotenv()

# Configuración
SQLITE_PATH = 'backend/data/qodeia.db'  # Ajusta si es diferente
SUPABASE_URL = os.getenv('DATABASE_URL')

if not SUPABASE_URL:
    print("❌ Error: DATABASE_URL no configurada en .env")
    exit(1)

# Conectar a ambas bases de datos
sqlite_engine = create_engine(f'sqlite:///{SQLITE_PATH}')
pg_engine = create_engine(SUPABASE_URL)

def migrate_table(table_name):
    """Migra una tabla de SQLite a PostgreSQL"""
    print(f"Migrando tabla: {table_name}")
    
    # Leer de SQLite
    metadata = MetaData()
    metadata.reflect(bind=sqlite_engine)
    
    if table_name not in metadata.tables:
        print(f"  ⚠️  Tabla {table_name} no existe en SQLite")
        return
    
    table = Table(table_name, metadata, autoload_with=sqlite_engine)
    
    # Crear en PostgreSQL
    table.create(pg_engine, checkfirst=True)
    
    # Copiar datos
    with sqlite_engine.connect() as source:
        rows = source.execute(table.select()).fetchall()
        if rows:
            with pg_engine.connect() as dest:
                dest.execute(table.insert(), [dict(row._mapping) for row in rows])
                dest.commit()
            print(f"  ✓ Migrados {len(rows)} registros")
        else:
            print(f"  ℹ️  Tabla vacía")

def main():
    print("🚀 Iniciando migración SQLite → Supabase\\n")
    
    # Lista de tablas a migrar
    tables = [
        'knowledge_graph',
        'credentials',
        'user_sessions',
        'cortex_logs'
    ]
    
    for table in tables:
        try:
            migrate_table(table)
        except Exception as e:
            print(f"  ❌ Error: {e}")
    
    print("\\n✅ Migración completada")
    print("\\n📝 Próximos pasos:")
    print("1. Verifica datos en Supabase SQL Editor")
    print("2. Actualiza .env con DATABASE_URL de Supabase")
    print("3. Redeploy en Vercel")

if __name__ == '__main__':
    main()`}
            />
          </div>

          <div>
            <h3 className="text-white font-bold mb-3">Ejecutar Migración</h3>
            <CodeBlock
              id="run_migrate"
              code={`# 1. Instalar dependencia adicional
pip install psycopg2-binary

# 2. Configurar DATABASE_URL en .env
echo "DATABASE_URL=postgresql://postgres:PASSWORD@db.xxx.supabase.co:5432/postgres" >> .env

# 3. Ejecutar script
python migrate_to_supabase.py

# 4. Verificar en Supabase
# Ve a https://app.supabase.com → SQL Editor → ejecuta:
# SELECT * FROM knowledge_graph LIMIT 10;`}
            />
          </div>
        </div>
      )
    },

    deploy: {
      icon: CheckCircle,
      title: 'Redeploy',
      content: (
        <div className="space-y-6">
          <div className="bg-green-900/20 border border-green-500 rounded-lg p-4">
            <h3 className="text-green-400 font-bold mb-2">Checklist Pre-Deploy</h3>
            <div className="space-y-2 text-green-200 text-sm">
              <label className="flex items-center gap-2">
                <input type="checkbox" className="w-4 h-4" />
                vercel.json actualizado
              </label>
              <label className="flex items-center gap-2">
                <input type="checkbox" className="w-4 h-4" />
                requirements.txt completo
              </label>
              <label className="flex items-center gap-2">
                <input type="checkbox" className="w-4 h-4" />
                Variables de entorno configuradas en Vercel
              </label>
              <label className="flex items-center gap-2">
                <input type="checkbox" className="w-4 h-4" />
                Migración a Supabase completada
              </label>
              <label className="flex items-center gap-2">
                <input type="checkbox" className="w-4 h-4" />
                database.py actualizado con PostgreSQL
              </label>
            </div>
          </div>

          <div>
            <h3 className="text-white font-bold mb-3">Comandos de Deploy</h3>
            <CodeBlock
              id="deploy_commands"
              code={`# Opción 1: Push a GitHub (auto-deploy)
git add .
git commit -m "fix: migrate to Supabase + fix Vercel config"
git push origin main

# Opción 2: Deploy directo con Vercel CLI
npm i -g vercel
vercel --prod

# Verificar deployment
vercel logs proyecto-ama-intent --follow`}
            />
          </div>

          <div>
            <h3 className="text-white font-bold mb-3">Test Post-Deploy</h3>
            <CodeBlock
              id="test_deploy"
              code={`# Test de salud del API
curl https://proyecto-ama-intent.vercel.app/api/health

# Test del endpoint principal
curl -X POST https://proyecto-ama-intent.vercel.app/api/chat \\
  -H "Content-Type: application/json" \\
  -d '{"message": "Hola AMA"}'

# Monitorear errores
# Ve a Vercel Dashboard → proyecto-ama-intent → Logs`}
            />
          </div>

          <div className="bg-blue-900/20 border border-blue-500 rounded-lg p-4">
            <h3 className="text-blue-400 font-bold mb-2">Troubleshooting</h3>
            <div className="space-y-2 text-blue-200 text-sm">
              <div>
                <strong>Si sigue fallando:</strong>
                <ul className="ml-4 mt-1 space-y-1">
                  <li>→ Revisa logs en Vercel Dashboard</li>
                  <li>→ Verifica que DATABASE_URL sea correcta</li>
                  <li>→ Confirma que Supabase permita conexiones externas</li>
                  <li>→ Aumenta maxDuration si hay timeouts</li>
                </ul>
              </div>
            </div>
          </div>
        </div>
      )
    }
  };

  const ActiveTab = tabs[activeTab];
  const Icon = ActiveTab.icon;

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-red-900 to-gray-900 p-6">
      <div className="max-w-5xl mx-auto">
        {/* Header */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center gap-3 bg-red-900/30 border border-red-500 rounded-full px-6 py-3 mb-4">
            <AlertTriangle size={24} className="text-red-400" />
            <span className="text-red-200 font-bold">Error Rate: 100%</span>
          </div>
          <h1 className="text-4xl font-bold text-white mb-2">
            Solución Deployment Vercel
          </h1>
          <p className="text-gray-400">proyecto-ama-intent</p>
        </div>

        {/* Tabs */}
        <div className="flex gap-2 mb-6 overflow-x-auto">
          {Object.entries(tabs).map(([key, tab]) => {
            const TabIcon = tab.icon;
            return (
              <button
                key={key}
                onClick={() => setActiveTab(key)}
                className={`flex items-center gap-2 px-4 py-2 rounded-lg transition whitespace-nowrap ${
                  activeTab === key
                    ? 'bg-blue-500 text-white'
                    : 'bg-gray-800 text-gray-400 hover:bg-gray-700'
                }`}
              >
                <TabIcon size={18} />
                {tab.title}
              </button>
            );
          })}
        </div>

        {/* Content */}
        <div className="bg-gray-800 rounded-xl shadow-2xl p-8 border border-gray-700">
          <div className="flex items-center gap-3 mb-6">
            <div className="p-3 bg-blue-500 rounded-lg">
              <Icon size={24} className="text-white" />
            </div>
            <h2 className="text-2xl font-bold text-white">{ActiveTab.title}</h2>
          </div>

          {ActiveTab.content}
        </div>

        {/* Quick Actions */}
        <div className="mt-6 grid grid-cols-1 md:grid-cols-3 gap-4">
          <a
            href="https://vercel.com/dgr198213-ui/proyecto-ama-intent/settings/environment-variables"
            target="_blank"
            rel="noopener noreferrer"
            className="bg-gray-800 border border-gray-700 rounded-lg p-4 hover:border-blue-500 transition"
          >
            <h3 className="text-white font-bold mb-1">Variables de Entorno</h3>
            <p className="text-gray-400 text-sm">Configurar en Vercel</p>
          </a>
          
          <a
            href="https://supabase.com/dashboard"
            target="_blank"
            rel="noopener noreferrer"
            className="bg-gray-800 border border-gray-700 rounded-lg p-4 hover:border-green-500 transition"
          >
            <h3 className="text-white font-bold mb-1">Supabase Dashboard</h3>
            <p className="text-gray-400 text-sm">Crear base de datos</p>
          </a>
          
          <a
            href="https://github.com/dgr198213-ui/proyecto-ama-intent"
            target="_blank"
            rel="noopener noreferrer"
            className="bg-gray-800 border border-gray-700 rounded-lg p-4 hover:border-purple-500 transition"
          >
            <h3 className="text-white font-bold mb-1">Repositorio GitHub</h3>
            <p className="text-gray-400 text-sm">Ver código fuente</p>
          </a>
        </div>
      </div>
    </div>
  );
}
