
import { argoFloatData, ArgoFloat } from './argo-data';

/**
 * Retrieves a single Argo float by its ID.
 * @param id The ID of the float to retrieve.
 * @returns The ArgoFloat object or undefined if not found.
 */
export function getArgoFloatById(id: string): ArgoFloat | undefined {
  return argoFloatData.find(float => float.id === id);
}
