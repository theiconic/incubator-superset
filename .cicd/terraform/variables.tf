variable "app_name" {}
variable "stack" {}
variable "project" {}
variable "cicd_cluster" {}
variable "cicd_namespace" {}
variable "db_endpoint" {}
variable "db_name" {}
variable "db_username" {}
variable "db_password" {}
variable "db_storage_size" {}

variable "aws_access_key_id" {}
variable "aws_secret_access_key" {}

variable "db_engine" {
  default = "mysql"
}

variable "db_engine_version" {
  default = "5.7.19"
}