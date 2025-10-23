"""Service category definitions and keywords."""
from typing import Dict, List
from functools import lru_cache

@lru_cache(maxsize=1)
def get_service_terms() -> Dict[str, List[str]]:
    """Returns expanded search terms for each service category."""
    return {
        "Load Balancers": _get_load_balancer_terms(),
        "Cloud Armor": _get_cloud_armor_terms(),
        "Private Service Connect (PSC)": _get_psc_terms()
    }

def _get_load_balancer_terms() -> List[str]:
    """Returns Load Balancer related terms."""
    return [
        "load balancer", "load balancing", "loadbalancer", "loadbalancing",
        "http load balancer", "https load balancer", "tcp load balancer",
        "udp load balancer", "internal load balancer", "external load balancer",
        "global load balancer", "regional load balancer", "application load balancer",
        "network load balancer", "lb", "glb", "alb", "nlb", "ilb",
        "forwarding rule", "forwardingrule", "target pool", "backend service",
        "backend bucket", "url map", "path matcher", "host rule", "load distribution",
        "health check", "healthcheck", "session affinity", "failover policy",
        "ssl certificate", "ssl policy", "target proxy", "cdn policy", "traffic director",
        "google_compute_forwarding_rule", "google_compute_global_forwarding_rule",
        "google_compute_target_pool", "google_compute_backend_service",
        "google_compute_backend_bucket", "google_compute_url_map",
        "google_compute_health_check", "google_compute_region_health_check",
        "google_compute_ssl_certificate", "google_compute_ssl_policy",
        "google_compute_target_http_proxy", "google_compute_target_https_proxy",
        "google_compute_target_tcp_proxy", "google_compute_target_ssl_proxy",
        "load", "balancer", "proxy", "forward", "routing", "balancing",
        "traffic routing", "http", "https", "ssl", "certificate", "health probe",
        "backend", "frontend", "ingress", "egress", "traffic distribution",
        "content delivery", "compute_forwarding", "compute_backend"
    ]

def _get_cloud_armor_terms() -> List[str]:
    """Returns Cloud Armor related terms."""
    return [
        "cloud armor", "security policy", "security rule", "web application firewall",
        "waf", "edge protection", "ddos protection", "attack protection",
        "security edge", "edge security",
        "security policy rule", "preconfigured waf", "rate limit", "recaptcha",
        "xss protection", "sql injection", "request throttling", "security header",
        "bot management", "adaptive protection", "named ip list", "threat intelligence",
        "google_compute_security_policy", "google_compute_security_policy_rule",
        "google_compute_region_security_policy", "google_compute_region_security_policy_rule",
        "google_network_security_gateway_security_policy",
        "google_compute_organization_security_policy",
        "google_compute_network_edge_security_service",
        "armor", "security", "policy", "protection", "firewall",
        "ddos", "attack", "rule", "edge protection", "application security",
        "traffic filtering", "web security", "request limiting", "compute_security",
        "network_security", "security_policy", "edge_security"
    ]

def _get_psc_terms() -> List[str]:
    """Returns Private Service Connect related terms."""
    return [
        "private service connect", "psc", "private endpoint", "service attachment",
        "private access", "private connectivity", "vpc peering", "network endpoint",
        "service perimeter", "vpc service controls", "vpc sc", "shared vpc",
        "private service access", "service networking connection", "peering connection",
        "reserved peering range", "allocated ip range", "service producer", "service consumer",
        "private connection", "vpc network peering", "network attachment", "service directory",
        "serverless vpc access", "vpc access connector", "private service link",
        "google_compute_service_attachment", "google_service_networking_connection",
        "google_compute_network_peering", "google_compute_global_address",
        "google_compute_shared_vpc_host_project", "google_compute_shared_vpc_service_project",
        "google_vpc_access_connector", "google_compute_network_peering_routes_config",
        "google_access_context_manager_service_perimeter",
        "private", "connect", "service", "vpc", "network", "peering",
        "attachment", "connectivity", "private networking", "service networking",
        "network peering", "compute_service", "service_networking", "network_peering",
        "shared_vpc", "vpc_access"
    ]

@lru_cache(maxsize=1)
def get_critical_keywords() -> Dict[str, List[str]]:
    """Returns critical keywords for quick pre-filtering."""
    return {
        "Load Balancers": [
            "load balancer", "loadbalancer", "load-balancer", "lb ", " lb,", "load balancing",
            "forwarding rule", "forwarding-rule", "target pool", "target-pool",
            "backend service", "backend-service", "url map", "url-map",
            "health check", "health-check", "ssl certificate", "ssl-certificate",
            "global forwarding", "regional forwarding",
            "compute_forwarding_rule", "compute_backend_service", "compute_url_map",
            "internal lb", "external lb", "application lb", "network lb", "http lb"
        ],
        "Cloud Armor": [
            "cloud armor", "cloud-armor", "cloudarmor", "security policy", "security-policy",
            "waf", "web application firewall", "ddos protection", "ddos-protection",
            "edge protection", "edge-protection", "security rule", "security-rule",
            "security edge", "security-edge", "compute_security_policy",
            "rate limiting", "rate-limiting", "recaptcha", "adaptive protection", "adaptive-protection"
        ],
        "Private Service Connect (PSC)": [
            "psc", "private service connect", "private-service-connect",
            "service attachment", "service-attachment", "vpc peering", "vpc-peering",
            "private endpoint", "private-endpoint", "service perimeter", "service-perimeter",
            "vpc service controls", "vpc-service-controls",
            "service networking connection", "service-networking-connection",
            "shared vpc", "shared-vpc", "vpc access connector", "vpc-access-connector",
            "compute_service_attachment", "service_networking_connection",
            "vpc sc", "network_peering", "network attachment", "network-attachment"
        ]
    }
