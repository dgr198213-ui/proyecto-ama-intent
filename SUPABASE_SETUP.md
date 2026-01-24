# Configuración de Supabase para AMA-Intent v3

Este documento explica cómo configurar Supabase como base de datos persistente para AMA-Intent v3.

## ¿Por qué Supabase?

En entornos serverless como Vercel, el filesystem es de solo lectura excepto `/tmp`, que es efímero. Supabase proporciona:
- ✅ Base de datos PostgreSQL persistente
- ✅ API RESTful automática
- ✅ Escalabilidad y rendimiento
- ✅ Capa gratuita generosa
- ✅ Backups automáticos

## Paso 1: Crear Proyecto en Supabase

1. Visita [supabase.com](https://supabase.com) y crea una cuenta
2. Crea un nuevo proyecto
3. Anota tu **Project URL** y **anon/public API key**

## Paso 2: Crear la Tabla en Supabase

Ejecuta el siguiente SQL en el SQL Editor de Supabase:

```sql
-- Crear tabla de interacciones
CREATE TABLE IF NOT EXISTS interactions (
    id BIGSERIAL PRIMARY KEY,
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    input TEXT NOT NULL,
    output TEXT NOT NULL,
    intent TEXT
);

-- Crear índices para mejor rendimiento
CREATE INDEX idx_interactions_timestamp ON interactions(timestamp DESC);
CREATE INDEX idx_interactions_intent ON interactions(intent);

-- Habilitar Row Level Security (opcional pero recomendado)
ALTER TABLE interactions ENABLE ROW LEVEL SECURITY;

-- Política para permitir todas las operaciones (ajusta según tus necesidades)
CREATE POLICY "Enable all access for service role" ON interactions
    FOR ALL
    USING (true)
    WITH CHECK (true);
```

## Paso 3: Configurar Variables de Entorno

### Para desarrollo local (.env):

```env
USE_SUPABASE=true
SUPABASE_URL=https://tu-proyecto.supabase.co
SUPABASE_KEY=tu-anon-key-aqui
```

### Para Vercel:

1. Ve a tu proyecto en Vercel Dashboard
2. Settings → Environment Variables
3. Añade:
   - `USE_SUPABASE` = `true`
   - `SUPABASE_URL` = `https://tu-proyecto.supabase.co`
   - `SUPABASE_KEY` = tu anon/service_role key

**Importante**: Usa la **service_role key** para operaciones administrativas, o la **anon key** con políticas RLS adecuadas.

## Paso 4: Verificar Conexión

Después de configurar, puedes verificar la conexión visitando:

```
http://tu-dominio.vercel.app/api/db/check
```

O desde el panel de administración:

```
http://tu-dominio.vercel.app/admin
```

Deberías ver:
- ✅ Tipo: SUPABASE
- ✅ Conexión: Supabase connection successful

## Función PostgreSQL Opcional (para estadísticas)

Para mejorar las estadísticas por intención, crea esta función:

```sql
CREATE OR REPLACE FUNCTION get_intent_counts()
RETURNS TABLE (intent TEXT, count BIGINT) AS $$
BEGIN
    RETURN QUERY
    SELECT i.intent, COUNT(*)::BIGINT as count
    FROM interactions i
    GROUP BY i.intent;
END;
$$ LANGUAGE plpgsql;
```

## Migración desde SQLite

Si tienes datos en SQLite local y quieres migrarlos a Supabase:

```python
import sqlite3
from supabase import create_client

# Conectar a SQLite
sqlite_conn = sqlite3.connect('data/ama_memory.db')
cursor = sqlite_conn.cursor()
cursor.execute("SELECT timestamp, input, output, intent FROM interactions")
rows = cursor.fetchall()

# Conectar a Supabase
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Migrar datos
for row in rows:
    supabase.table("interactions").insert({
        "timestamp": row[0],
        "input": row[1],
        "output": row[2],
        "intent": row[3]
    }).execute()

print(f"✅ Migrados {len(rows)} registros")
```

## Troubleshooting

### Error: "Table 'interactions' does not exist"
- Verifica que ejecutaste el SQL del Paso 2
- Revisa que el nombre de la tabla sea exactamente `interactions`

### Error: "JWT expired" o "Invalid API key"
- Verifica que tu SUPABASE_KEY sea válida
- Asegúrate de no haber cambiado las claves en Supabase

### Error: "Row Level Security policy violation"
- Desactiva RLS temporalmente o crea políticas adecuadas
- Usa service_role key para bypass RLS (solo en servidor)

## Seguridad

⚠️ **Importante**:
- Nunca expongas tu `service_role` key públicamente
- Usa `anon` key con políticas RLS para acceso público
- Configura políticas RLS adecuadas en producción
- Considera autenticación adicional para operaciones sensibles

## Costos

Supabase Free Tier incluye:
- 500 MB de base de datos
- 1 GB de transferencia
- 50,000 solicitudes mensuales

Para AMA-Intent v3, esto es más que suficiente para comenzar.

## Soporte

Para más información:
- [Documentación de Supabase](https://supabase.com/docs)
- [Supabase Python Client](https://supabase.com/docs/reference/python/introduction)
