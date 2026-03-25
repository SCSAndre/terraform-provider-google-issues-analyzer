"""Service category definitions and keywords."""
from typing import Dict, List
from functools import lru_cache


SUPPORTED_SERVICE_CATEGORIES: List[str] = ["Cloud Armor"]


def get_supported_service_categories() -> List[str]:
    """Returns the explicitly supported service categories."""
    return list(SUPPORTED_SERVICE_CATEGORIES)

@lru_cache(maxsize=1)
def get_service_terms() -> Dict[str, List[str]]:
    """Returns expanded search terms for supported service categories."""
    return {SUPPORTED_SERVICE_CATEGORIES[0]: _get_cloud_armor_terms()}

def _get_cloud_armor_terms() -> List[str]:
    """Returns Cloud Armor related terms."""
    return [
        "cloud armor", "security policy", "security rule", "web application firewall",
        "waf", "ddos protection", "attack protection",
        "security edge", "edge security",
        "security policy rule", "preconfigured waf", "rate limit", "recaptcha",
        "xss protection", "sql injection", "request throttling", "security header",
        "bot management", "adaptive protection", "named ip list", "threat intelligence",
        "google_compute_security_policy", "google_compute_security_policy_rule",
        "google_compute_region_security_policy", "google_compute_region_security_policy_rule",
        "google_network_security_gateway_security_policy",
        "google_compute_organization_security_policy",
        "google_network_security_security_profile",
        "google_network_security_security_profile_group",
        "google_compute_network_edge_security_service",
        "modsecurity", "owasp", "cve rule", "sqli detection", "xss detection",
        "rce detection", "lfi detection", "scanner detection", "protocol attack",
        "php injection", "session fixation", "preconfigured rule", "sensitivity level",
        "rule sensitivity", "low sensitivity", "medium sensitivity", "high sensitivity",
        "paranoia level", "adaptive protection", "ml-based detection",
        "auto-deploy threshold", "load threshold", "confidence threshold",
        "named ip list", "bot management", "bot score", "recaptcha enterprise",
        "recaptcha token action", "captcha action", "managed protection",
        "managed protection plus", "cloud armor enterprise", "preview mode",
        "enforced mode", "rate-based ban", "ban duration", "rate limit threshold",
        "exceed action", "rate limit key", "conform action", "xff header",
        "true client ip"
    ]

@lru_cache(maxsize=1)
def get_critical_keywords() -> Dict[str, List[str]]:
    """Returns critical keywords for quick pre-filtering."""
    return {
        SUPPORTED_SERVICE_CATEGORIES[0]: [
            "cloud armor", "cloud-armor", "cloudarmor", "security policy", "security-policy",
            "waf", "web application firewall", "ddos protection", "ddos-protection",
            "security rule", "security-rule",
            "security edge", "security-edge", "compute_security_policy",
            "rate limiting", "rate-limiting", "recaptcha", "adaptive protection", "adaptive-protection",
            "google_compute_security_policy", "google_compute_region_security_policy",
            "google_compute_region_security_policy_rule", "google_network_security_gateway_security_policy",
            "google_network_security_security_profile", "google_network_security_security_profile_group",
            "google_compute_network_edge_security_service", "modsecurity", "owasp", "preconfigured rule",
            "managed protection", "cloud armor enterprise", "rate-based ban", "bot management"
        ]
    }
