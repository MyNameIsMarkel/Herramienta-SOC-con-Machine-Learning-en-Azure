variable "resource_group_name" {
  description = "Nombre del Resource Group en Azure"
  default     = "rg-soc-proyecto"
}

variable "location" {
  description = "Región de Azure"
  default     = "francecentral"
}

variable "workspace_name" {
  description = "Nombre del Log Analytics Workspace"
  default     = "log-soc-ml"
}

variable "ml_endpoint_url" {
  description = "URL del endpoint ML de detección de anomalías"
  type        = string
}

variable "ml_endpoint_key" {
  description = "Clave de autenticación del endpoint ML"
  type        = string
  sensitive   = true
}