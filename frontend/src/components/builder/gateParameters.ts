import { ANGLE_LIMIT } from '../../types/catalog.generated';
import { formatAngle, gateSpec, parseAngle, PARAMETER_NAMES } from '../../services/circuit';
import type { CircuitGateName, CustomCircuitGate } from '../../types/api';

export type ParameterName = (typeof PARAMETER_NAMES)[number];
export type ParameterText = Record<ParameterName, string>;

export const PARAMETER_LABELS: Record<ParameterName, string> = { angle: 'θ (theta)', phi: 'φ (phi)', lam: 'λ (lambda)' };

export function operandLabels(name: CircuitGateName): string[] {
  const count = gateSpec(name).qubits;
  if (count === 1) return ['Qubit'];
  if (name === 'SWAP') return ['First qubit', 'Second qubit'];
  if (count === 2) return ['Control qubit', 'Target qubit'];
  return ['First control', 'Second control', 'Target qubit'];
}

export function parameterNames(name: CircuitGateName): ParameterName[] {
  const count = gateSpec(name).params;
  return PARAMETER_NAMES.slice(0, count === 3 ? 3 : count);
}

/** Parses the parameter fields a gate needs; returns an error message when one is invalid. */
export function parseParameters(name: CircuitGateName, text: ParameterText): Partial<CustomCircuitGate> | string {
  const values: Partial<CustomCircuitGate> = {};
  for (const key of parameterNames(name)) {
    const value = parseAngle(text[key]);
    if (value === null) return `Enter ${PARAMETER_LABELS[key]} as a number or a π expression such as pi/2.`;
    if (Math.abs(value) > ANGLE_LIMIT) return 'Angles must be between −2π and 2π radians.';
    values[key] = value;
  }
  return values;
}

export function parameterText(gate?: CustomCircuitGate): ParameterText {
  return {
    angle: gate?.angle !== undefined ? formatAngle(gate.angle) : 'π/2',
    phi: gate?.phi !== undefined ? formatAngle(gate.phi) : '0',
    lam: gate?.lam !== undefined ? formatAngle(gate.lam) : '0',
  };
}
