export interface DiagnosisResult {
  code: string
  name: string
  conclusion: "买入" | "观望" | null
  reason: string
  close: number | null
  open: number | null
  pct_chg: number | null
  ema20: number | null
  error?: string
  source?: string
  klinePath?: string
  klineDate?: string
  backtestBarsPath?: string
  backtestSummaryPath?: string
}

export interface StrategyConfigItem {
  key: string
  label: string
  type: "int" | "float"
  default: number
  min?: number
  max?: number
  step?: number
  description: string
}

export interface StrategyInfo {
  id: string
  name: string
  description: string
  configSchema: StrategyConfigItem[]
}

export interface StockDiagnosis {
  codes: string[]
  sector?: string
  days: number
  strategy: string
  strategyConfig: Record<string, any>
  skills: string[]
  skillNames: string[]
  initialPrompt: string
  results: DiagnosisResult[]
  successCount: number
  failedCount: number
}

export interface SectorInfo {
  code: string
  name: string
  type?: string  // "行业" | "概念"
}

export interface BacktestSummary {
  stock_code: string
  stock_name: string
  initial_capital: number
  final_capital: number
  total_return: number
  max_drawdown: number
  win_rate: number
  trade_count: number
}

export interface BacktestBar {
  date: string
  stock_name: string
  open: number
  close: number
  signal: string | null
  cost: number | null
  profit: number | null
  capital: number
  stop_loss: number | null
  target_price: number | null
}

export interface StockSearchResult {
  code: string
  name: string
  type: string
}
