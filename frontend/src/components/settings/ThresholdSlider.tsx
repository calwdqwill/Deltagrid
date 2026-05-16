"use client";

interface ThresholdSliderProps {
  label: string;
  value: number;
  min?: number;
  max?: number;
  step?: number;
  onChange: (value: number) => void;
}

export function ThresholdSlider({
  label,
  value,
  min = 0,
  max = 5,
  step = 0.1,
  onChange,
}: ThresholdSliderProps) {
  return (
    <div>
      <label className="block text-sm font-medium text-secondary-text mb-1.5">{label}</label>
      <div className="flex items-center gap-3">
        <input
          type="range"
          min={min}
          max={max}
          step={step}
          value={value}
          onChange={(e) => onChange(parseFloat(e.target.value))}
          className="flex-1 accent-accent-blue"
        />
        <span className="w-16 text-right text-sm font-medium text-primary-text tabular-nums">
          {value.toFixed(step < 0.1 ? 2 : 1)}%
        </span>
      </div>
    </div>
  );
}
