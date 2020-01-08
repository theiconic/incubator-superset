output "db_instance_id" {
  value = "${aws_db_instance.superset.id}"
}

output "db_instance_address" {
  value = "${aws_db_instance.superset.address}"
}

output "redis_instance_address" {
  value = "${aws_elasticache_cluster.superset.cache_nodes.0.address}"
}