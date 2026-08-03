from fastapi import APIRouter, Depends
from pydantic import BaseModel
from uuid import UUID
from app.models.user import User
from app.api.deps import get_current_user

router = APIRouter(prefix="/impact", tags=["Impact Analysis"])


class ImpactRequest(BaseModel):
    requirement_id: str
    max_depth: int = 3


@router.post("/analyze", summary="BFS impact analysis for a changed requirement")
def analyze_impact(
    data: ImpactRequest,
    current_user: User = Depends(get_current_user),
):
    """
    Runs BFS on Neo4j graph starting from a Requirement node.
    depth_1 = modules that directly implement this requirement  -> HIGH impact
    depth_2 = modules that depend on depth_1                   -> MEDIUM impact
    depth_3 = test cases / distant modules                     -> LOW impact
    """
    from app.services.neo4j_service import bfs_impact
    result = bfs_impact(req_id=data.requirement_id, max_depth=data.max_depth)
    return {
        "requirement_id": data.requirement_id,
        "impact":         result,
        "summary":        f"{result['total_affected']} modules affected across {data.max_depth} levels",
    }


@router.get("/project/{project_id}/stats",
            summary="Get Neo4j graph node counts for a project")
def graph_stats(
    project_id: UUID,
    current_user: User = Depends(get_current_user),
):
    from app.services.neo4j_service import get_project_graph_stats
    return {
        "project_id":  str(project_id),
        "graph_stats": get_project_graph_stats(str(project_id)),
    }
