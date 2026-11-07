import { MEASUREMENT_BASES, NOISE_PROFILES } from '../types/catalog.generated';
import type { MeasurementBasis, NoiseProfile, NoiseProfileInfo } from '../types/api';
import { isNoiseProfile } from '../services/circuit';

/** Noise presets and calibrated device snapshots, grouped for the select menu. */
export function NoiseProfileSelect({ value, onChange, profiles, label = 'Simulator noise', disabled }: {
  value: NoiseProfile;
  onChange: (value: NoiseProfile) => void;
  profiles?: NoiseProfileInfo[];
  label?: string;
  disabled?: boolean;
}) {
  const options = profiles?.length ? profiles : NOISE_PROFILES;
  const presets = options.filter((profile) => profile.kind === 'preset');
  const devices = options.filter((profile) => profile.kind === 'device');
  return (
    <label className="text-sm">
      {label}
      <select className="input mt-2" value={value} disabled={disabled}
        onChange={(event) => { if (isNoiseProfile(event.target.value)) onChange(event.target.value); }}>
        <optgroup label="Preset noise">
          {presets.map((profile) => <option key={profile.id} value={profile.id}>{profile.label}</option>)}
        </optgroup>
        {devices.length > 0 && <optgroup label="Real-device noise models (no IBM account needed)">
          {devices.map((profile) => <option key={profile.id} value={profile.id}>{profile.label}</option>)}
        </optgroup>}
      </select>
      {options.find((profile) => profile.id === value)?.kind === 'device' && <span className="mt-1 block text-xs text-slate-400">
        Uses a published calibration snapshot: realistic gate errors, readout errors, and qubit connectivity.
      </span>}
    </label>
  );
}

const BASIS_HELP: Record<MeasurementBasis, string> = {
  Z: 'Z (computational)',
  X: 'X (rotate with H)',
  Y: 'Y (rotate with S† then H)',
};

/** Chooses a measurement basis for each qubit. */
export function MeasurementBasisPicker({ bases, onChange, qubits, disabled }: {
  bases: MeasurementBasis[];
  onChange: (bases: MeasurementBasis[]) => void;
  /** Qubits that are measured; defaults to all. */
  qubits?: number[];
  disabled?: boolean;
}) {
  const shown = qubits ?? bases.map((_, index) => index);
  return (
    <fieldset className="text-sm" disabled={disabled}>
      <legend>Measurement basis</legend>
      <div className="mt-2 grid gap-2 sm:grid-cols-2">
        {shown.map((qubit) => (
          <label key={qubit} className="flex items-center gap-2">
            <span className="w-8 font-mono text-slate-300">q{qubit}</span>
            <select className="input" aria-label={`Measurement basis for q${qubit}`} value={bases[qubit] ?? 'Z'}
              onChange={(event) => {
                const next = [...bases];
                next[qubit] = event.target.value as MeasurementBasis;
                onChange(next);
              }}>
              {MEASUREMENT_BASES.map((basis) => <option key={basis} value={basis}>{BASIS_HELP[basis]}</option>)}
            </select>
          </label>
        ))}
      </div>
      <p className="mt-2 text-xs text-slate-400">
        Measuring in X or Y reveals phase information that a Z histogram hides. Ideal probabilities update to match.
      </p>
    </fieldset>
  );
}
