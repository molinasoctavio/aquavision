# 🌊 AquaVision Analytics

**El Veo.com del Waterpolo** — Sistema completo de grabación, análisis IA y gestión de video deportivo especializado en waterpolo.

---

## ✨ Características

| Módulo | Descripción |
|--------|-------------|
| 📹 **VideoIngestionAgent** | Acepta video de cualquier fuente: cámara, smartphone, YouTube, RTMP/RTSP, drones |
| ⚙️ **VideoProcessingAgent** | Transcoding H.264, estabilización SteadyView, HLS adaptativo multi-calidad |
| 🤖 **WaterpoloAIDetectionAgent** | YOLOv8 especializado: detección de pelota, jugadores, cascos, eventos automáticos |
| 📊 **AnalyticsEngineAgent** | Posesión, heatmaps, shot maps, momentum, superioridades, estadísticas por período |
| 🎬 **ClipGenerationAgent** | Clips automáticos por evento + editor manual con follow-cam y keyframes |
| ✏️ **DrawingAnnotationAgent** | Flechas, líneas, zonas, texto, dibujo libre sobre el video en pausa o play |
| 📡 **LiveStreamAgent** | Streaming a YouTube/Twitch/Facebook con overlay, bookmarks desde el móvil |
| 🔗 **SharingExportAgent** | Links públicos/privados, exportación social (Instagram, TikTok, Twitter) |
| 👤 **PlayerSpotlightAgent** | Perfil individual, heatmap por jugador, detección OCR de número de casquete |
| 💬 **CoachAssistAgent** | Claude AI para análisis conversacional: "¿Cuántos tiros en superioridad?" |
| 👥 **TeamManagementAgent** | Equipos, jugadores (cap 1–13), temporadas, torneos, alineaciones |
| 💾 **StorageOrchestrationAgent** | MinIO/S3, CDN, cola de procesamiento, retención configurable |

---

## 🚀 Inicio Rápido (1 comando)

### Prerrequisitos
- Docker Desktop instalado
- 8 GB RAM mínimo recomendado

```bash
# 1. Clonar/abrir el directorio
cd aquavision

# 2. Configurar variables de entorno
cp .env.example .env
# → Edita .env y agrega tu ANTHROPIC_API_KEY

# 3. Levantar todo el stack
docker-compose up --build

# 4. Abrir la aplicación
#    Web:          http://localhost:80
#    API Docs:     http://localhost:8000/api/docs
#    MinIO:        http://localhost:9001  (minioadmin/minioadmin)
#    Flower:       http://localhost:5555
```

**Primera vez:**
1. Ve a `http://localhost` → regístrate como entrenador
2. Crea un equipo con tus jugadores
3. Sube un video desde la página **"Subir Video"**
4. Espera el procesamiento (barra de progreso en tiempo real)
5. Abre el **Editor AquaVision** para ver eventos detectados
6. Ve a **Estadísticas** para el dashboard completo de analytics
7. Usa el **CoachAssist** para preguntar sobre el partido en lenguaje natural

---

## 📁 Estructura del Proyecto

```
aquavision/
├── agents/                     # 8+ Agentes IA especializados
│   ├── base_agent.py           # Clase base con Redis queue
│   ├── video_ingestion_agent.py
│   ├── video_processing_agent.py   # FFmpeg + estabilización
│   ├── waterpolo_detection_agent.py # YOLOv8 + state machine
│   ├── analytics_engine_agent.py   # Estadísticas completas
│   ├── clip_generation_agent.py
│   ├── player_spotlight_agent.py
│   ├── sharing_export_agent.py
│   └── db_writer_agent.py
│
├── api/                        # Backend FastAPI
│   ├── app/
│   │   ├── main.py             # App entry point
│   │   ├── config.py           # Settings con pydantic-settings
│   │   ├── database.py         # SQLAlchemy async
│   │   ├── models/             # 15+ modelos de BD
│   │   ├── schemas/            # Pydantic schemas
│   │   ├── routers/            # REST endpoints
│   │   ├── services/           # CoachAssist, Storage, Queue
│   │   └── middleware/         # JWT auth, rate limiting
│   └── migrations/             # Alembic (2 versiones)
│
├── frontend/                   # Next.js 14 + TypeScript
│   └── src/
│       ├── app/
│       │   ├── dashboard/      # Panel principal
│       │   ├── upload/         # Subida de videos (drag & drop)
│       │   ├── editor/[id]/    # AquaEditor con Video.js
│       │   ├── matches/        # Gestión de partidos
│       │   ├── analytics/[id]/ # Dashboard de estadísticas
│       │   └── auth/           # Login / Register
│       └── components/
│           ├── video/          # VideoPlayer (Video.js + HLS)
│           ├── editor/         # EventFeed, ClipPanel, DrawingCanvas (Konva)
│           ├── analytics/      # PoolShotMap, Heatmap, Momentum, CoachAssist
│           └── layout/         # Sidebar, AppShell
│
├── worker/                     # Celery + queue consumer
│   ├── celery_app.py
│   ├── tasks.py                # Tareas async
│   └── queue_consumer.py       # Redis queue loop
│
├── ml/                         # Modelos AI
│   └── models/                 # YOLO weights (waterpolo_yolo.pt)
│
├── infrastructure/
│   ├── docker/                 # Dockerfiles (api, worker, frontend)
│   ├── nginx/                  # Reverse proxy + media delivery
│   └── mediamtx/               # RTMP/RTSP/WebRTC server config
│
├── tests/                      # Tests unitarios e integración
│   ├── test_api.py
│   └── test_agents.py
│
├── docker-compose.yml          # Stack completo (9 servicios)
├── .env.example                # Variables de entorno
└── README.md
```

---

## 🏊 Flujo de Procesamiento de Video

```
1. Upload (Web/URL/RTMP)
        ↓
2. VideoIngestionAgent     → Normaliza formato, descarga URL, graba stream
        ↓
3. VideoProcessingAgent    → Transcode H.264 → SteadyView → HLS multi-bitrate
        ↓
4. WaterpoloAIDetectionAgent → YOLOv8: pelota, jugadores, eventos → JSON
        ↓
5. AnalyticsEngineAgent    → Posesión, heatmaps, shots, momentum → Analytics
        ↓
6. ClipGenerationAgent     → Clips automáticos por cada evento detectado
        ↓
7. DBWriterAgent           → Persiste todo en PostgreSQL
        ↓
8. [Opcional] CoachAssistAgent → Claude API genera resumen + responde preguntas
```

---

## 🎮 Guía de Uso

### Subir un Video
- Arrastra y suelta cualquier MP4/MOV/AVI
- O pega una URL de YouTube
- Selecciona el partido al que corresponde
- El sistema procesa automáticamente en background

### Editor AquaVision
- Barra de tiempo con marcadores de colores por tipo de evento
- Click en evento → salta al momento exacto
- Botón tijera → marca inicio/fin de clip
- Lápiz → activa dibujo sobre el video (flechas, zonas, texto)
- Panel derecho: Eventos | Clips | Dibujo

### Analytics Dashboard
- **Resumen**: marcador, estadísticas comparativas, por período
- **Lanzamientos**: mapa 2D de la piscina con todos los tiros
- **Heatmap**: densidad de posicionamiento por equipo
- **Momentum**: gráfica de flujo del partido
- **CoachAssist IA**: chat en lenguaje natural con Claude

### Live Streaming
- Ve a **En Vivo** → Iniciar Transmisión
- Copia la URL RTMP + stream key en OBS/tu cámara
- Bookmark eventos en tiempo real desde el móvil

---

## ⚙️ Configuración Avanzada

### Modelo YOLO Fine-tuned (opcional)
Para mejores resultados de detección, entrena un modelo con tus propios videos:
```bash
# Coloca el modelo en:
ml/models/waterpolo_yolo.pt

# O configura en .env:
YOLO_MODEL_PATH=ml/models/waterpolo_yolo.pt
YOLO_CONFIDENCE_THRESHOLD=0.5
```

### Cámaras IP Fijas
Agrega en la BD con streaming RTSP:
```bash
# Via API:
POST /api/v1/teams/{team_id}/cameras
{
  "name": "Cámara Piscina",
  "camera_type": "fixed",
  "stream_url": "rtsp://192.168.1.100/stream"
}
```

---

## 🔌 API REST

Documentación interactiva: `http://localhost:8000/api/docs`

Endpoints principales:
- `POST /api/v1/auth/register` — Registro
- `POST /api/v1/auth/login` — Login (JWT)
- `POST /api/v1/videos/upload` — Subir video
- `POST /api/v1/videos/ingest-url` — Ingerir desde URL
- `GET /api/v1/videos/{id}/status` — Estado de procesamiento
- `GET /api/v1/analytics/matches/{id}` — Analytics del partido
- `POST /api/v1/analytics/coach-assist` — Query a CoachAssist IA
- `POST /api/v1/livestream/start` — Iniciar stream en vivo

---

## 🧪 Tests

```bash
# En el contenedor API:
docker-compose exec api pytest tests/ -v

# Localmente:
cd aquavision
pip install -r api/requirements.txt
pytest tests/ -v
```

---

## 📦 Stack Tecnológico

| Capa | Tecnología |
|------|-----------|
| Backend | Python 3.11, FastAPI, SQLAlchemy 2.0, Alembic |
| Workers | Celery, Redis, queue_consumer multi-agent |
| Base de datos | PostgreSQL 16 |
| Almacenamiento | MinIO (compatible S3) |
| Video | FFmpeg, vidstab, Video.js, HLS.js |
| IA Detección | YOLOv8 (Ultralytics), OpenCV, NumPy |
| IA Análisis | Anthropic Claude (claude-sonnet-4) |
| Frontend | Next.js 14, React 18, TypeScript, Tailwind CSS |
| Visualización | Recharts, Konva.js (drawing), D3.js |
| Streaming | MediaMTX (RTMP/RTSP/WebRTC), Nginx |
| Infra | Docker Compose, Nginx reverse proxy |
| CI/CD | GitHub Actions |

---

## 📄 Licencia

MIT — Construido con ❤️ para la comunidad del waterpolo mundial.

*AquaVision Analytics — "El Veo.com del Waterpolo"*
