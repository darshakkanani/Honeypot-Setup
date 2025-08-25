#!/usr/bin/env python3
"""
SecureHoney Geolocation Service
IP geolocation and geographic analysis for attack attribution
"""

import requests
import geoip2.database
import geoip2.errors
from typing import Dict, Any, Optional, List
import logging
from pathlib import Path
import json
from datetime import datetime
from models import DatabaseManager, GeolocationData

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GeolocationService:
    """IP geolocation and geographic intelligence service"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
        self.geoip_db_path = Path(__file__).parent / "GeoLite2-City.mmdb"
        self.cache = {}
        
    def get_ip_location(self, ip_address: str, use_cache: bool = True) -> Dict[str, Any]:
        """Get comprehensive geolocation data for IP address"""
        
        # Check cache first
        if use_cache and ip_address in self.cache:
            return self.cache[ip_address]
        
        # Check database
        location_data = self._get_from_database(ip_address)
        if location_data and use_cache:
            self.cache[ip_address] = location_data
            return location_data
        
        # Get from external sources
        location_data = self._fetch_location_data(ip_address)
        
        # Save to database
        if location_data:
            self._save_to_database(ip_address, location_data)
            if use_cache:
                self.cache[ip_address] = location_data
        
        return location_data or self._get_default_location()
    
    def _get_from_database(self, ip_address: str) -> Optional[Dict[str, Any]]:
        """Get location data from database"""
        session = self.db.get_session()
        try:
            geo_data = session.query(GeolocationData).filter(
                GeolocationData.ip_address == ip_address
            ).first()
            
            if geo_data:
                return {
                    'ip': geo_data.ip_address,
                    'country': geo_data.country,
                    'country_code': geo_data.country_code,
                    'region': geo_data.region,
                    'city': geo_data.city,
                    'latitude': geo_data.latitude,
                    'longitude': geo_data.longitude,
                    'timezone': geo_data.timezone,
                    'isp': geo_data.isp,
                    'organization': geo_data.organization,
                    'asn': geo_data.asn,
                    'is_proxy': geo_data.is_proxy,
                    'is_tor': geo_data.is_tor,
                    'is_vpn': geo_data.is_vpn,
                    'last_updated': geo_data.last_updated.isoformat()
                }
            return None
            
        finally:
            self.db.close_session(session)
    
    def _fetch_location_data(self, ip_address: str) -> Optional[Dict[str, Any]]:
        """Fetch location data from multiple sources"""
        
        # Try MaxMind GeoIP2 database first (if available)
        geoip_data = self._get_from_geoip2(ip_address)
        if geoip_data:
            return geoip_data
        
        # Try free IP geolocation APIs
        api_data = self._get_from_api(ip_address)
        if api_data:
            return api_data
        
        return None
    
    def _get_from_geoip2(self, ip_address: str) -> Optional[Dict[str, Any]]:
        """Get location from MaxMind GeoIP2 database"""
        if not self.geoip_db_path.exists():
            return None
        
        try:
            with geoip2.database.Reader(str(self.geoip_db_path)) as reader:
                response = reader.city(ip_address)
                
                return {
                    'ip': ip_address,
                    'country': response.country.name or 'Unknown',
                    'country_code': response.country.iso_code or 'XX',
                    'region': response.subdivisions.most_specific.name or 'Unknown',
                    'city': response.city.name or 'Unknown',
                    'latitude': float(response.location.latitude) if response.location.latitude else 0.0,
                    'longitude': float(response.location.longitude) if response.location.longitude else 0.0,
                    'timezone': response.location.time_zone or 'Unknown',
                    'isp': 'Unknown',
                    'organization': 'Unknown',
                    'asn': 'Unknown',
                    'is_proxy': False,
                    'is_tor': False,
                    'is_vpn': False,
                    'source': 'geoip2'
                }
                
        except (geoip2.errors.AddressNotFoundError, Exception) as e:
            logger.debug(f"GeoIP2 lookup failed for {ip_address}: {e}")
            return None
    
    def _get_from_api(self, ip_address: str) -> Optional[Dict[str, Any]]:
        """Get location from free IP geolocation API"""
        try:
            # Using ip-api.com (free tier: 1000 requests/month)
            response = requests.get(
                f"http://ip-api.com/json/{ip_address}",
                timeout=5
            )
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get('status') == 'success':
                    return {
                        'ip': ip_address,
                        'country': data.get('country', 'Unknown'),
                        'country_code': data.get('countryCode', 'XX'),
                        'region': data.get('regionName', 'Unknown'),
                        'city': data.get('city', 'Unknown'),
                        'latitude': float(data.get('lat', 0)),
                        'longitude': float(data.get('lon', 0)),
                        'timezone': data.get('timezone', 'Unknown'),
                        'isp': data.get('isp', 'Unknown'),
                        'organization': data.get('org', 'Unknown'),
                        'asn': data.get('as', 'Unknown'),
                        'is_proxy': data.get('proxy', False),
                        'is_tor': False,  # Not provided by this API
                        'is_vpn': False,  # Not provided by this API
                        'source': 'ip-api'
                    }
            
        except Exception as e:
            logger.error(f"API geolocation failed for {ip_address}: {e}")
        
        return None
    
    def _save_to_database(self, ip_address: str, location_data: Dict[str, Any]):
        """Save location data to database"""
        session = self.db.get_session()
        try:
            # Check if record exists
            existing = session.query(GeolocationData).filter(
                GeolocationData.ip_address == ip_address
            ).first()
            
            if existing:
                # Update existing record
                existing.country = location_data.get('country')
                existing.country_code = location_data.get('country_code')
                existing.region = location_data.get('region')
                existing.city = location_data.get('city')
                existing.latitude = location_data.get('latitude')
                existing.longitude = location_data.get('longitude')
                existing.timezone = location_data.get('timezone')
                existing.isp = location_data.get('isp')
                existing.organization = location_data.get('organization')
                existing.asn = location_data.get('asn')
                existing.is_proxy = location_data.get('is_proxy', False)
                existing.is_tor = location_data.get('is_tor', False)
                existing.is_vpn = location_data.get('is_vpn', False)
                existing.last_updated = datetime.utcnow()
            else:
                # Create new record
                geo_data = GeolocationData(
                    ip_address=ip_address,
                    country=location_data.get('country'),
                    country_code=location_data.get('country_code'),
                    region=location_data.get('region'),
                    city=location_data.get('city'),
                    latitude=location_data.get('latitude'),
                    longitude=location_data.get('longitude'),
                    timezone=location_data.get('timezone'),
                    isp=location_data.get('isp'),
                    organization=location_data.get('organization'),
                    asn=location_data.get('asn'),
                    is_proxy=location_data.get('is_proxy', False),
                    is_tor=location_data.get('is_tor', False),
                    is_vpn=location_data.get('is_vpn', False)
                )
                session.add(geo_data)
            
            session.commit()
            
        except Exception as e:
            session.rollback()
            logger.error(f"Failed to save geolocation data: {e}")
        finally:
            self.db.close_session(session)
    
    def _get_default_location(self) -> Dict[str, Any]:
        """Get default location data for unknown IPs"""
        return {
            'ip': 'unknown',
            'country': 'Unknown',
            'country_code': 'XX',
            'region': 'Unknown',
            'city': 'Unknown',
            'latitude': 0.0,
            'longitude': 0.0,
            'timezone': 'Unknown',
            'isp': 'Unknown',
            'organization': 'Unknown',
            'asn': 'Unknown',
            'is_proxy': False,
            'is_tor': False,
            'is_vpn': False,
            'source': 'default'
        }
    
    def analyze_geographic_patterns(self, days: int = 30) -> Dict[str, Any]:
        """Analyze geographic attack patterns"""
        session = self.db.get_session()
        try:
            from models import Attack
            from sqlalchemy import func
            from datetime import timedelta
            
            # Get attacks from last N days
            since_date = datetime.utcnow() - timedelta(days=days)
            
            # Get attack counts by country
            country_attacks = session.query(
                GeolocationData.country,
                GeolocationData.country_code,
                func.count(Attack.id).label('attack_count')
            ).join(
                Attack, GeolocationData.ip_address == Attack.source_ip
            ).filter(
                Attack.timestamp >= since_date
            ).group_by(
                GeolocationData.country, GeolocationData.country_code
            ).order_by(
                func.count(Attack.id).desc()
            ).all()
            
            # Get unique attackers by country
            country_attackers = session.query(
                GeolocationData.country,
                func.count(func.distinct(Attack.source_ip)).label('unique_attackers')
            ).join(
                Attack, GeolocationData.ip_address == Attack.source_ip
            ).filter(
                Attack.timestamp >= since_date
            ).group_by(
                GeolocationData.country
            ).all()
            
            # Combine data
            geographic_data = {}
            for country, country_code, attack_count in country_attacks:
                geographic_data[country] = {
                    'country_code': country_code,
                    'total_attacks': attack_count,
                    'unique_attackers': 0
                }
            
            for country, unique_attackers in country_attackers:
                if country in geographic_data:
                    geographic_data[country]['unique_attackers'] = unique_attackers
            
            # Calculate risk scores
            total_attacks = sum(data['total_attacks'] for data in geographic_data.values())
            for country_data in geographic_data.values():
                country_data['attack_percentage'] = (
                    country_data['total_attacks'] / total_attacks * 100 
                    if total_attacks > 0 else 0
                )
                country_data['risk_score'] = self._calculate_country_risk_score(country_data)
            
            return {
                'analysis_period_days': days,
                'total_countries': len(geographic_data),
                'total_attacks_analyzed': total_attacks,
                'country_statistics': geographic_data,
                'top_threat_countries': sorted(
                    geographic_data.items(),
                    key=lambda x: x[1]['risk_score'],
                    reverse=True
                )[:10]
            }
            
        finally:
            self.db.close_session(session)
    
    def _calculate_country_risk_score(self, country_data: Dict[str, Any]) -> float:
        """Calculate risk score for a country based on attack patterns"""
        score = 0
        
        # Base score from attack count
        score += min(country_data['total_attacks'] * 0.1, 50)
        
        # Bonus for high attacker diversity
        if country_data['unique_attackers'] > 0:
            diversity_ratio = country_data['total_attacks'] / country_data['unique_attackers']
            if diversity_ratio > 10:  # Many attacks from few IPs (botnet indicator)
                score += 20
            elif diversity_ratio > 5:
                score += 10
        
        # Bonus for high attack percentage
        if country_data['attack_percentage'] > 20:
            score += 15
        elif country_data['attack_percentage'] > 10:
            score += 10
        elif country_data['attack_percentage'] > 5:
            score += 5
        
        return min(score, 100)
    
    def get_attack_heatmap_data(self) -> List[Dict[str, Any]]:
        """Get data for geographic attack heatmap visualization"""
        session = self.db.get_session()
        try:
            from models import Attack
            from sqlalchemy import func
            
            # Get attack counts by coordinates
            heatmap_data = session.query(
                GeolocationData.latitude,
                GeolocationData.longitude,
                GeolocationData.country,
                GeolocationData.city,
                func.count(Attack.id).label('attack_count')
            ).join(
                Attack, GeolocationData.ip_address == Attack.source_ip
            ).filter(
                GeolocationData.latitude != 0,
                GeolocationData.longitude != 0
            ).group_by(
                GeolocationData.latitude,
                GeolocationData.longitude,
                GeolocationData.country,
                GeolocationData.city
            ).all()
            
            return [
                {
                    'lat': float(lat),
                    'lng': float(lng),
                    'country': country,
                    'city': city,
                    'intensity': min(attack_count / 10, 1.0),  # Normalize for heatmap
                    'attack_count': attack_count
                }
                for lat, lng, country, city, attack_count in heatmap_data
                if lat and lng
            ]
            
        finally:
            self.db.close_session(session)

# Initialize geolocation service
def get_geolocation_service(db_manager: DatabaseManager) -> GeolocationService:
    """Get geolocation service instance"""
    return GeolocationService(db_manager)
