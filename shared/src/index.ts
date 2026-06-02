export interface PensionBenefit {
  enabled: boolean
  monthly_amount: number
  start_age: number
  amount_in_today_reais: boolean
}

export interface PrivatePensionBenefit extends PensionBenefit {
  modality: 'lifetime' | 'fixed_term'
  term_years: number | null
}

export interface SimulationParameters {
  current_age: number
  current_patrimony: number
  monthly_contribution: number
  desired_monthly_income: number
  retirement_age: number
  life_expectancy: number
  inflation_rate: number
  annual_real_return: number
  safe_withdrawal_rate: number
  public_pension: PensionBenefit
  private_pension: PrivatePensionBenefit
}
