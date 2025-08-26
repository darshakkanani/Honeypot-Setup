"""
Advanced Threat Intelligence Integration
Real-time threat feeds, IOC matching, and attribution analysis
"""

import asyncio
import aiohttp
import hashlib
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Set
import structlog
from pathlib import Path
import geoip2.database
import geoip2.errors

from ..core.config import config
from ..core.redis import RedisCache

logger = structlog.get_logger()

class ThreatIntelligence:
    """Advanced threat intelligence engine"""
    
    def __init__(self):
        self.threat_feeds = {
            "malware_domains": "https://malware-filter.gitlab.io/malware-filter/urlhaus-filter-domains.txt",
            "tor_exits": "https://check.torproject.org/torbulkexitlist",
            "abuse_ch": "https://feodotracker.abuse.ch/downloads/ipblocklist.csv",
            "emerging_threats": "https://rules.emergingthreats.net/fwrules/emerging-Block-IPs.txt",
            "spamhaus": "https://www.spamhaus.org/drop/drop.txt"
        }
        
        self.ioc_database = {
            "malicious_ips": set(),
            "malicious_domains": set(),
            "malicious_hashes": set(),
            "tor_exits": set(),
            "known_botnets": set()
        }
        
        self.geoip_db = None
        self.threat_scores = {}
        self.attribution_data = {}
        
        # APT and threat actor signatures
        self.apt_signatures = self._load_apt_signatures()
        
        # Threat intelligence cache
        self.cache_ttl = 3600  # 1 hour
        
    async def initialize(self):
        """Initialize threat intelligence feeds and databases"""
        try:
            # Load GeoIP database
            await self._load_geoip_database()
            
            # Update threat feeds
            await self._update_threat_feeds()
            
            # Load cached IOCs
            await self._load_cached_iocs()
            
            logger.info("threat_intelligence_initialized", 
                       feeds=len(self.threat_feeds),
                       malicious_ips=len(self.ioc_database["malicious_ips"]))
                       
        except Exception as e:
            logger.error("threat_intelligence_init_failed", error=str(e))
    
    async def enrich_attack(self, attack_data: Dict[str, Any]) -> Dict[str, Any]:
        """Enrich attack data with threat intelligence"""
        try:
            source_ip = attack_data.get("source_ip")
            if not source_ip:
                return {}
            
            # Check cache first
            cache_key = f"threat_intel:{source_ip}"
            cached = await RedisCache.get(cache_key)
            if cached:
                return json.loads(cached)
            
            enrichment = {
                "source_ip": source_ip,
                "timestamp": datetime.utcnow().isoformat(),
                "threat_score": 0.0,
                "risk_factors": [],
                "attribution": {},
                "ioc_matches": [],
                "geolocation": {},
                "reputation": {},
                "behavioral_indicators": {}
            }
            
            # IOC matching
            ioc_results = await self._check_iocs(source_ip)
            enrichment.update(ioc_results)
            
            # Geolocation analysis
            geo_data = await self._get_geolocation(source_ip)
            enrichment["geolocation"] = geo_data
            
            # Reputation analysis
            reputation = await self._check_reputation(source_ip)
            enrichment["reputation"] = reputation
            
            # APT attribution
            attribution = await self._analyze_attribution(attack_data)
            enrichment["attribution"] = attribution
            
            # Behavioral analysis
            behavioral = await self._analyze_behavioral_indicators(attack_data)
            enrichment["behavioral_indicators"] = behavioral
            
            # Calculate overall threat score
            threat_score = await self._calculate_threat_score(enrichment)
            enrichment["threat_score"] = threat_score
            
            # Cache results
            await RedisCache.set(cache_key, json.dumps(enrichment), expire=self.cache_ttl)
            
            logger.info("attack_enriched", 
                       source_ip=source_ip,
                       threat_score=threat_score,
                       ioc_matches=len(enrichment["ioc_matches"]))
            
            return enrichment
            
        except Exception as e:
            logger.error("attack_enrichment_failed", 
                        source_ip=attack_data.get("source_ip"), 
                        error=str(e))
            return {}
    
    async def _check_iocs(self, ip_address: str) -> Dict[str, Any]:
        """Check IP against IOC databases"""
        try:
            ioc_matches = []
            risk_factors = []
            
            # Check malicious IPs
            if ip_address in self.ioc_database["malicious_ips"]:
                ioc_matches.append({
                    "type": "malicious_ip",
                    "source": "threat_feeds",
                    "confidence": 0.9,
                    "description": "IP found in malicious IP feeds"
                })
                risk_factors.append("known_malicious_ip")
            
            # Check Tor exit nodes
            if ip_address in self.ioc_database["tor_exits"]:
                ioc_matches.append({
                    "type": "tor_exit",
                    "source": "tor_project",
                    "confidence": 1.0,
                    "description": "Tor exit node"
                })
                risk_factors.append("tor_exit_node")
            
            # Check botnet IPs
            if ip_address in self.ioc_database["known_botnets"]:
                ioc_matches.append({
                    "type": "botnet",
                    "source": "botnet_feeds",
                    "confidence": 0.8,
                    "description": "Known botnet member"
                })
                risk_factors.append("botnet_member")
            
            # Additional IOC checks
            additional_checks = await self._advanced_ioc_checks(ip_address)
            ioc_matches.extend(additional_checks["matches"])
            risk_factors.extend(additional_checks["risk_factors"])
            
            return {
                "ioc_matches": ioc_matches,
                "risk_factors": risk_factors,
                "is_known_malicious": len([m for m in ioc_matches if m["type"] == "malicious_ip"]) > 0,
                "is_tor_exit": len([m for m in ioc_matches if m["type"] == "tor_exit"]) > 0,
                "is_botnet": len([m for m in ioc_matches if m["type"] == "botnet"]) > 0
            }
            
        except Exception as e:
            logger.error("ioc_check_failed", ip=ip_address, error=str(e))
            return {"ioc_matches": [], "risk_factors": []}
    
    async def _advanced_ioc_checks(self, ip_address: str) -> Dict[str, Any]:
        """Perform advanced IOC checks using external APIs"""
        matches = []
        risk_factors = []
        
        try:
            # VirusTotal API check
            vt_result = await self._check_virustotal(ip_address)
            if vt_result.get("malicious", False):
                matches.append({
                    "type": "virustotal_detection",
                    "source": "virustotal",
                    "confidence": vt_result.get("confidence", 0.7),
                    "description": f"Detected by {vt_result.get('detections', 0)} engines"
                })
                risk_factors.append("virustotal_detection")
            
            # AbuseIPDB check
            abuse_result = await self._check_abuseipdb(ip_address)
            if abuse_result.get("abuse_confidence", 0) > 50:
                matches.append({
                    "type": "abuse_reports",
                    "source": "abuseipdb",
                    "confidence": abuse_result.get("abuse_confidence", 0) / 100,
                    "description": f"Abuse confidence: {abuse_result.get('abuse_confidence', 0)}%"
                })
                risk_factors.append("abuse_reports")
            
            # Shodan check
            shodan_result = await self._check_shodan(ip_address)
            if shodan_result.get("suspicious_services", []):
                matches.append({
                    "type": "suspicious_services",
                    "source": "shodan",
                    "confidence": 0.6,
                    "description": f"Suspicious services: {', '.join(shodan_result['suspicious_services'])}"
                })
                risk_factors.append("suspicious_services")
            
        except Exception as e:
            logger.error("advanced_ioc_check_failed", ip=ip_address, error=str(e))
        
        return {"matches": matches, "risk_factors": risk_factors}
    
    async def _get_geolocation(self, ip_address: str) -> Dict[str, Any]:
        """Get detailed geolocation information"""
        try:
            if not self.geoip_db:
                return {}
            
            response = self.geoip_db.city(ip_address)
            
            geo_data = {
                "country": response.country.name,
                "country_code": response.country.iso_code,
                "city": response.city.name,
                "region": response.subdivisions.most_specific.name,
                "postal_code": response.postal.code,
                "latitude": float(response.location.latitude) if response.location.latitude else None,
                "longitude": float(response.location.longitude) if response.location.longitude else None,
                "timezone": response.location.time_zone,
                "isp": getattr(response, 'traits', {}).get('isp', 'Unknown'),
                "organization": getattr(response, 'traits', {}).get('organization', 'Unknown'),
                "accuracy_radius": response.location.accuracy_radius
            }
            
            # Add risk assessment based on location
            geo_data["location_risk"] = self._assess_location_risk(geo_data)
            
            return geo_data
            
        except geoip2.errors.AddressNotFoundError:
            return {"error": "IP address not found in GeoIP database"}
        except Exception as e:
            logger.error("geolocation_failed", ip=ip_address, error=str(e))
            return {}
    
    async def _check_reputation(self, ip_address: str) -> Dict[str, Any]:
        """Check IP reputation across multiple sources"""
        try:
            reputation_data = {
                "overall_score": 0.0,
                "sources": {},
                "categories": [],
                "last_seen": None,
                "first_seen": None
            }
            
            # Check multiple reputation sources
            sources = [
                ("spamhaus", self._check_spamhaus_reputation),
                ("barracuda", self._check_barracuda_reputation),
                ("talos", self._check_talos_reputation)
            ]
            
            scores = []
            for source_name, check_func in sources:
                try:
                    result = await check_func(ip_address)
                    reputation_data["sources"][source_name] = result
                    if result.get("score") is not None:
                        scores.append(result["score"])
                    if result.get("categories"):
                        reputation_data["categories"].extend(result["categories"])
                except Exception as e:
                    logger.error(f"{source_name}_reputation_failed", ip=ip_address, error=str(e))
            
            # Calculate overall reputation score
            if scores:
                reputation_data["overall_score"] = sum(scores) / len(scores)
            
            # Remove duplicate categories
            reputation_data["categories"] = list(set(reputation_data["categories"]))
            
            return reputation_data
            
        except Exception as e:
            logger.error("reputation_check_failed", ip=ip_address, error=str(e))
            return {}
    
    async def _analyze_attribution(self, attack_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze attack for APT/threat actor attribution"""
        try:
            attribution = {
                "possible_actors": [],
                "confidence": 0.0,
                "indicators": [],
                "campaigns": [],
                "ttps": []
            }
            
            # Extract attack characteristics
            attack_type = attack_data.get("attack_type", "")
            user_agent = attack_data.get("user_agent", "")
            payload = attack_data.get("raw_payload", "")
            target_port = attack_data.get("target_port", 0)
            
            # Check against APT signatures
            for apt_name, signatures in self.apt_signatures.items():
                matches = 0
                matched_indicators = []
                
                # Check user agent patterns
                if "user_agents" in signatures:
                    for ua_pattern in signatures["user_agents"]:
                        if ua_pattern.lower() in user_agent.lower():
                            matches += 1
                            matched_indicators.append(f"User-Agent: {ua_pattern}")
                
                # Check payload patterns
                if "payload_patterns" in signatures:
                    for pattern in signatures["payload_patterns"]:
                        if pattern.lower() in payload.lower():
                            matches += 1
                            matched_indicators.append(f"Payload pattern: {pattern}")
                
                # Check TTP patterns
                if "ttps" in signatures:
                    for ttp in signatures["ttps"]:
                        if ttp.get("attack_type") == attack_type:
                            if target_port in ttp.get("ports", []):
                                matches += 1
                                matched_indicators.append(f"TTP: {ttp['description']}")
                
                # Calculate confidence based on matches
                total_indicators = len(signatures.get("user_agents", [])) + \
                                 len(signatures.get("payload_patterns", [])) + \
                                 len(signatures.get("ttps", []))
                
                if total_indicators > 0:
                    confidence = matches / total_indicators
                    
                    if confidence > 0.3:  # Threshold for possible attribution
                        attribution["possible_actors"].append({
                            "name": apt_name,
                            "confidence": confidence,
                            "matched_indicators": matched_indicators,
                            "description": signatures.get("description", "")
                        })
            
            # Sort by confidence
            attribution["possible_actors"].sort(key=lambda x: x["confidence"], reverse=True)
            
            # Set overall confidence to highest individual confidence
            if attribution["possible_actors"]:
                attribution["confidence"] = attribution["possible_actors"][0]["confidence"]
            
            return attribution
            
        except Exception as e:
            logger.error("attribution_analysis_failed", error=str(e))
            return {}
    
    async def _analyze_behavioral_indicators(self, attack_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze behavioral indicators for threat classification"""
        try:
            indicators = {
                "automation_score": 0.0,
                "sophistication_score": 0.0,
                "persistence_score": 0.0,
                "evasion_techniques": [],
                "tool_signatures": []
            }
            
            # Analyze timing patterns
            timing_analysis = await self._analyze_timing_patterns(attack_data)
            indicators["automation_score"] = timing_analysis.get("automation_score", 0.0)
            
            # Analyze payload sophistication
            payload_analysis = await self._analyze_payload_sophistication(attack_data)
            indicators["sophistication_score"] = payload_analysis.get("sophistication_score", 0.0)
            
            # Detect evasion techniques
            evasion_techniques = await self._detect_evasion_techniques(attack_data)
            indicators["evasion_techniques"] = evasion_techniques
            
            # Identify tool signatures
            tool_signatures = await self._identify_tool_signatures(attack_data)
            indicators["tool_signatures"] = tool_signatures
            
            return indicators
            
        except Exception as e:
            logger.error("behavioral_analysis_failed", error=str(e))
            return {}
    
    async def _calculate_threat_score(self, enrichment_data: Dict[str, Any]) -> float:
        """Calculate overall threat score from all intelligence sources"""
        try:
            score_components = []
            
            # IOC matches score
            ioc_score = len(enrichment_data.get("ioc_matches", [])) * 0.2
            score_components.append(min(ioc_score, 1.0))
            
            # Reputation score
            reputation = enrichment_data.get("reputation", {})
            rep_score = 1.0 - reputation.get("overall_score", 0.5)
            score_components.append(rep_score)
            
            # Attribution confidence
            attribution = enrichment_data.get("attribution", {})
            attr_score = attribution.get("confidence", 0.0)
            score_components.append(attr_score)
            
            # Behavioral indicators
            behavioral = enrichment_data.get("behavioral_indicators", {})
            behav_score = (
                behavioral.get("automation_score", 0.0) * 0.3 +
                behavioral.get("sophistication_score", 0.0) * 0.4 +
                behavioral.get("persistence_score", 0.0) * 0.3
            )
            score_components.append(behav_score)
            
            # Location risk
            geo_data = enrichment_data.get("geolocation", {})
            location_risk = geo_data.get("location_risk", 0.0)
            score_components.append(location_risk)
            
            # Calculate weighted average
            if score_components:
                threat_score = sum(score_components) / len(score_components)
            else:
                threat_score = 0.0
            
            return min(max(threat_score, 0.0), 1.0)
            
        except Exception as e:
            logger.error("threat_score_calculation_failed", error=str(e))
            return 0.5
    
    async def _update_threat_feeds(self):
        """Update threat intelligence feeds"""
        try:
            logger.info("updating_threat_feeds")
            
            async with aiohttp.ClientSession() as session:
                for feed_name, feed_url in self.threat_feeds.items():
                    try:
                        await self._update_single_feed(session, feed_name, feed_url)
                    except Exception as e:
                        logger.error("feed_update_failed", feed=feed_name, error=str(e))
            
            # Cache updated IOCs
            await self._cache_iocs()
            
            logger.info("threat_feeds_updated", 
                       malicious_ips=len(self.ioc_database["malicious_ips"]),
                       tor_exits=len(self.ioc_database["tor_exits"]))
                       
        except Exception as e:
            logger.error("threat_feeds_update_failed", error=str(e))
    
    def _load_apt_signatures(self) -> Dict[str, Any]:
        """Load APT and threat actor signatures"""
        return {
            "APT1": {
                "description": "Chinese APT group",
                "user_agents": ["Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1)"],
                "payload_patterns": ["comment.php", "index.asp"],
                "ttps": [
                    {"attack_type": "HTTP_INJECTION", "ports": [80, 443], "description": "Web shell deployment"}
                ]
            },
            "Lazarus": {
                "description": "North Korean APT group",
                "user_agents": ["Mozilla/5.0 (Windows NT 6.1; WOW64; Trident/7.0; rv:11.0)"],
                "payload_patterns": ["wscript.exe", "powershell.exe"],
                "ttps": [
                    {"attack_type": "MALWARE", "ports": [80, 8080], "description": "Banking trojan deployment"}
                ]
            },
            "Cozy_Bear": {
                "description": "Russian APT group (APT29)",
                "user_agents": ["Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.1; Trident/5.0)"],
                "payload_patterns": ["SeaDuke", "CozyDuke"],
                "ttps": [
                    {"attack_type": "SPEAR_PHISHING", "ports": [443], "description": "Spear phishing campaigns"}
                ]
            }
        }
    
    # Additional helper methods would be implemented here...
    # (Placeholder implementations for brevity)
    
    async def _check_virustotal(self, ip_address: str) -> Dict[str, Any]:
        """Check IP against VirusTotal API"""
        # Implementation would use VirusTotal API
        return {"malicious": False, "confidence": 0.0, "detections": 0}
    
    async def _check_abuseipdb(self, ip_address: str) -> Dict[str, Any]:
        """Check IP against AbuseIPDB"""
        # Implementation would use AbuseIPDB API
        return {"abuse_confidence": 0}
    
    async def _check_shodan(self, ip_address: str) -> Dict[str, Any]:
        """Check IP against Shodan"""
        # Implementation would use Shodan API
        return {"suspicious_services": []}

# Global threat intelligence instance
threat_intelligence = ThreatIntelligence()

# Convenience functions
async def enrich_attack_with_threat_intel(attack_data: Dict[str, Any]) -> Dict[str, Any]:
    """Enrich attack with threat intelligence"""
    return await threat_intelligence.enrich_attack(attack_data)

async def update_threat_feeds():
    """Update all threat intelligence feeds"""
    await threat_intelligence._update_threat_feeds()

async def check_ip_reputation(ip_address: str) -> Dict[str, Any]:
    """Check IP reputation"""
    return await threat_intelligence._check_reputation(ip_address)
