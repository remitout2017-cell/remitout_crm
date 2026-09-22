import type { Place } from '../../types'
import { Input } from '../../components/ui/Input'

/** Edubao's `[location]/[city]/[state]/[country]/[iso]` place shape, reused for birth place & passport issue place. */
export function PlaceFields({ label, value, onChange }: { label: string; value: Place; onChange: (p: Place) => void }) {
  const set = (k: keyof Place) => (e: React.ChangeEvent<HTMLInputElement>) => onChange({ ...value, [k]: e.target.value })
  return (
    <fieldset className="grid gap-3 sm:grid-cols-2">
      <legend className="col-span-full mb-1 text-xs font-semibold uppercase tracking-wide text-muted">{label}</legend>
      <Input label="Location (city, state, country)" required value={value.location} onChange={set('location')} className="sm:col-span-2" />
      <Input label="City" required value={value.city} onChange={set('city')} />
      <Input label="State" required value={value.state} onChange={set('state')} />
      <Input label="Country" required value={value.country} onChange={set('country')} />
      <Input label="Country ISO" required value={value.iso} onChange={set('iso')} maxLength={3} />
    </fieldset>
  )
}
