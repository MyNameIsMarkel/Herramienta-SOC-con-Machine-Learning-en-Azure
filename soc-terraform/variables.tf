variable "resource_group_name" {
  default = "rg-soc-proyecto"
}

variable "location" {
  description = "Región permitida en tu suscripción de estudiante"
  default     = "norwayeast"  # Cambia esto por tu región permitida
}

variable "workspace_name" {
  default = "law-soc-workspace"
}
