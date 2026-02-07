"""
Centralized transaction coordinator for managing complex multi-domain operations.
"""
from typing import Dict, Any, Callable, Optional, List, Union
from contextlib import asynccontextmanager
import logging
from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession
from .uow import UnitOfWork


logger = logging.getLogger(__name__)


class TransactionCoordinator:
    """
    Centralized transaction coordinator that manages complex operations
    spanning multiple domains and repositories.
    """
    
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]):
        self.session_factory = session_factory
    
    @asynccontextmanager
    async def coordinated_transaction(self):
        """Context manager for coordinated transactions."""
        async with UnitOfWork(self.session_factory) as uow:
            yield uow
    
    async def execute_coordinated_operation(
        self,
        operations: List[Callable],
        rollback_handler: Optional[Callable] = None
    ) -> Dict[str, Any]:
        """
        Execute multiple coordinated operations within a single transaction.
        
        Args:
            operations: List of async functions to execute
            rollback_handler: Optional handler to call on rollback
            
        Returns:
            Dictionary with results and metadata
        """
        results = []
        operation_names = []
        
        try:
            async with self.coordinated_transaction() as uow:
                for i, operation in enumerate(operations):
                    try:
                        # Execute the operation with the UoW
                        result = await operation(uow)
                        results.append(result)
                        operation_names.append(operation.__name__ if hasattr(operation, '__name__') else f"operation_{i}")
                    except Exception as e:
                        logger.error(f"Operation {operation.__name__ if hasattr(operation, '__name__') else f'operation_{i}'} failed: {e}")
                        raise
                
                # Commit all operations together
                await uow.commit()
                
                return {
                    "success": True,
                    "results": results,
                    "operation_names": operation_names,
                    "total_operations": len(operations)
                }
                
        except Exception as e:
            logger.error(f"Coordinated transaction failed: {e}")
            
            if rollback_handler:
                try:
                    await rollback_handler(e, results)
                except Exception as rh_error:
                    logger.error(f"Rollback handler failed: {rh_error}")
            
            return {
                "success": False,
                "error": str(e),
                "results_so_far": results,
                "failed_at_operation": len(results)
            }
    
    async def execute_complex_workflow(
        self,
        workflow_steps: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Execute a complex workflow with multiple steps and dependencies.
        
        Args:
            workflow_steps: List of workflow steps with conditions and operations
            
        Returns:
            Workflow execution results
        """
        results = {}
        
        try:
            async with self.coordinated_transaction() as uow:
                for step_idx, step in enumerate(workflow_steps):
                    step_name = step.get("name", f"step_{step_idx}")
                    operation = step.get("operation")
                    condition = step.get("condition")
                    rollback_operation = step.get("rollback_operation")
                    
                    # Check condition if provided
                    if condition and not await condition(results):
                        logger.info(f"Skipping step {step_name} due to condition not met")
                        results[step_name] = {"skipped": True, "reason": "condition_not_met"}
                        continue
                    
                    try:
                        # Execute the operation
                        step_result = await operation(uow, results)
                        results[step_name] = {"success": True, "data": step_result}
                        
                    except Exception as e:
                        logger.error(f"Workflow step {step_name} failed: {e}")
                        
                        # Execute rollback operation if provided
                        if rollback_operation:
                            try:
                                rollback_result = await rollback_operation(uow, results, e)
                                results[step_name] = {
                                    "success": False,
                                    "error": str(e),
                                    "rolled_back": True,
                                    "rollback_result": rollback_result
                                }
                            except Exception as rb_error:
                                logger.error(f"Rollback operation for step {step_name} failed: {rb_error}")
                                results[step_name] = {
                                    "success": False,
                                    "error": str(e),
                                    "rolled_back": False,
                                    "rollback_error": str(rb_error)
                                }
                                raise
                        else:
                            results[step_name] = {
                                "success": False,
                                "error": str(e)
                            }
                            raise
                
                # Commit all changes if we got here
                await uow.commit()
                
                return {
                    "workflow_completed": True,
                    "results": results,
                    "total_steps": len(workflow_steps)
                }
                
        except Exception as e:
            logger.error(f"Complex workflow failed: {e}")
            return {
                "workflow_completed": False,
                "error": str(e),
                "partial_results": results
            }


class MultiDomainTransactionService:
    """
    Service for handling transactions that span multiple domains.
    """
    
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]):
        self.coordinator = TransactionCoordinator(session_factory)
    
    async def update_asteroid_with_related_entities(
        self,
        asteroid_id: int,
        asteroid_updates: Dict[str, Any],
        related_approaches: Optional[List[Dict[str, Any]]] = None,
        related_threats: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Update an asteroid and related entities in a single coordinated transaction.
        """
        async def update_asteroid_op(uow):
            from domains.asteroid.repositories.asteroid_repository import AsteroidRepository
            repo = uow.get_repository(AsteroidRepository)
            asteroid = await repo.get(asteroid_id)
            if not asteroid:
                raise ValueError(f"Asteroid with ID {asteroid_id} not found")
            
            # Update asteroid attributes
            for key, value in asteroid_updates.items():
                setattr(asteroid, key, value)
            
            return await repo.update(asteroid)
        
        async def update_approaches_op(uow):
            if not related_approaches:
                return []
            
            from domains.approach.repositories.approach_repository import ApproachRepository
            from domains.approach.models.close_approach import CloseApproachModel
            repo = uow.get_repository(ApproachRepository)
            results = []
            
            for approach_data in related_approaches:
                approach_data['asteroid_id'] = asteroid_id  # Link to asteroid
                approach = CloseApproachModel(**approach_data)
                approach = await repo.add(approach)
                results.append(approach)
            
            return results
            
        async def update_threats_op(uow):
            if not related_threats:
                return []
            
            from domains.threat.repositories.threat_repository import ThreatRepository
            from domains.threat.models.threat_assessment import ThreatAssessmentModel
            repo = uow.get_repository(ThreatRepository)
            results = []
            
            for threat_data in related_threats:
                threat_data['asteroid_id'] = asteroid_id  # Link to asteroid
                threat = ThreatAssessmentModel(**threat_data)
                threat = await repo.add(threat)
                results.append(threat)
            
            return results
        
        operations = [update_asteroid_op]
        if related_approaches:
            operations.append(update_approaches_op)
        if related_threats:
            operations.append(update_threats_op)
        
        return await self.coordinator.execute_coordinated_operation(operations)
    
    async def batch_process_asteroids(
        self,
        asteroid_data_list: List[Dict[str, Any]],
        validate_each: bool = True
    ) -> Dict[str, Any]:
        """
        Process multiple asteroids in a single transaction with validation.
        """
        async def validate_and_create_asteroid(uow, data):
            # In a real implementation, you'd have validation logic here
            if validate_each:
                # Example validation: check that required fields are present
                required_fields = ['designation', 'absolute_magnitude', 'estimated_diameter_km']
                for field in required_fields:
                    if field not in data:
                        raise ValueError(f"Missing required field: {field}")
            
            from domains.asteroid.repositories.asteroid_repository import AsteroidRepository
            repo = uow.get_repository(AsteroidRepository)
            asteroid = await repo.add(type('obj', (object,), data)())
            return asteroid
        
        operations = [
            lambda uow: validate_and_create_asteroid(uow, data)
            for data in asteroid_data_list
        ]
        
        return await self.coordinator.execute_coordinated_operation(operations)


# Global transaction coordinator instance
_transaction_coordinator: Optional[TransactionCoordinator] = None


def get_transaction_coordinator(session_factory: async_sessionmaker[AsyncSession]) -> TransactionCoordinator:
    """Get or create a transaction coordinator instance."""
    global _transaction_coordinator
    if _transaction_coordinator is None:
        _transaction_coordinator = TransactionCoordinator(session_factory)
    return _transaction_coordinator