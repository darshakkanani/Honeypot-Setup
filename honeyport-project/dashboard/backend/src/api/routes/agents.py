"""
Agents API routes
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import List, Dict, Any
import logging

from ..models import AgentResponse, AgentStatus
from ..main import database, get_current_user

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/", response_model=Dict[str, Any])
async def get_agents(user: dict = Depends(get_current_user)):
    """Get all honeypot agents status"""
    try:
        agents = await database.get_agents()
        
        # Calculate summary stats
        total_agents = len(agents)
        online_agents = len([a for a in agents if a.get('status') == 'online'])
        
        return {
            "agents": agents,
            "total_agents": total_agents,
            "online_agents": online_agents,
            "offline_agents": total_agents - online_agents
        }
        
    except Exception as e:
        logger.error(f"Error getting agents: {e}")
        raise HTTPException(status_code=500, detail="Failed to get agents")

@router.get("/{agent_id}")
async def get_agent(agent_id: str, user: dict = Depends(get_current_user)):
    """Get specific agent details"""
    try:
        agents = await database.get_agents()
        agent = next((a for a in agents if a.get('agent_id') == agent_id), None)
        
        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")
        
        return agent
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting agent {agent_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to get agent")

@router.post("/{agent_id}/status")
async def update_agent_status(
    agent_id: str,
    status_data: Dict[str, Any],
    user: dict = Depends(get_current_user)
):
    """Update agent status"""
    try:
        await database.update_agent_status(
            agent_id=agent_id,
            status=status_data.get('status', 'unknown'),
            version=status_data.get('version'),
            location=status_data.get('location'),
            listeners=status_data.get('listeners', [])
        )
        
        return {"message": f"Agent {agent_id} status updated"}
        
    except Exception as e:
        logger.error(f"Error updating agent status: {e}")
        raise HTTPException(status_code=500, detail="Failed to update agent status")

@router.get("/stats/summary")
async def get_agent_stats(user: dict = Depends(get_current_user)):
    """Get agent statistics summary"""
    try:
        agents = await database.get_agents()
        
        stats = {
            "total_agents": len(agents),
            "status_distribution": {},
            "version_distribution": {},
            "location_distribution": {}
        }
        
        for agent in agents:
            # Status distribution
            status = agent.get('status', 'unknown')
            stats['status_distribution'][status] = stats['status_distribution'].get(status, 0) + 1
            
            # Version distribution
            version = agent.get('version', 'unknown')
            stats['version_distribution'][version] = stats['version_distribution'].get(version, 0) + 1
            
            # Location distribution
            location = agent.get('location', 'unknown')
            stats['location_distribution'][location] = stats['location_distribution'].get(location, 0) + 1
        
        return stats
        
    except Exception as e:
        logger.error(f"Error getting agent stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to get agent stats")
