variable "resource_group_name" {
  description = "Nombre del Resource Group en Azure"
  default     = "rg-soc-proyecto"
}

variable "location" {
  description = "Región de Azure permitida en tu suscripción de estudiante"
  default     = "francecentral"
}

variable "workspace_name" {
  description = "Nombre del Log Analytics Workspace"
  default     = "log-soc-ml"
}