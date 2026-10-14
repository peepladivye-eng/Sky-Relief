// Shared TypeScript types matching Python schemas

export interface SkyEvent {
  event_id: string
  name: string
  bbox: [number, number, number, number]
  before_date: string
  after_date: string
  sensor: string
  water_db?: number
}

export interface FloodStats {
  area_km2: number
  pct_of_bbox: number
  unknown_fraction: number
  geojson: object
}

export interface VisionCheck {
  mask_plausible: boolean
  false_positive_notes: string[]
  damage_observations: string[]
  caveats: string[]
  confidence: number
}

export interface Weather {
  peak_mm: number
  three_day_mm: number
  anomaly: boolean
  series: { date: string; mm: number }[]
}

export interface Report {
  id: string
  text: string
  source: string
  source_url?: string
  place?: string
  lat?: number
  lon?: number
  need?: string
  urgency?: number
  count?: number
  status?: string
}

export interface Exposure {
  settlement: string
  lat: number
  lon: number
  flood_fraction: number
  facilities: string[]
  road_flooded: boolean
  silent_flooded: boolean
}

export interface Priority {
  rank: number
  settlement: string
  score: number
  reasons: string[]
  sources: string[]
  recommended_action: string
}

export interface Sitrep {
  event: SkyEvent
  flood: FloodStats
  vision: VisionCheck
  weather: Weather
  reports: Report[]
  exposures: Exposure[]
  priorities: Priority[]
  summary_en: string
  summary_hi: string
  whatsapp_brief_en: string
  whatsapp_brief_hi: string
  limitations: string[]
}

export type StepStatus = 'running' | 'done' | 'error'

export interface StepEvent {
  type: 'step'
  tool: string
  status: StepStatus
  detail: string
  ts: number
}

export interface SitrepEvent {
  type: 'sitrep'
  data: Sitrep
}

export interface ErrorEvent {
  type: 'error'
  detail: string
}

// Partial data emitted during long-running tool execution
export interface PartialEvent {
  type: 'partial'
  tool: string
  phase: string  // e.g., "reading_raster", "computing_mask", "extracting_reports"
  progress?: number  // 0-100 percentage
  detail?: string
}

export type AgentEvent = StepEvent | SitrepEvent | ErrorEvent | PartialEvent