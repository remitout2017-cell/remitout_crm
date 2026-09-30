import { useEffect, useState } from 'react'
import type { Place } from '../../types'
import { Input } from '../../components/ui/Input'
import { Autocomplete } from '../../components/ui/Autocomplete'
import { useGetCountriesQuery } from '../reference/api'
import { ALL_CITIES, INDIA_PLACES, INDIA_STATES } from '../students/indiaPlaces'

const ISO_PATTERN = /^[A-Z]{3}$/
// Title-case each word, e.g. "united states" -> "United States".
const toTitleCase = (v: string) => v.replace(/\w\S*/g, (w) => w[0].toUpperCase() + w.slice(1).toLowerCase())

/** Edubao's `[location]/[city]/[state]/[country]/[iso]` place shape, reused for birth place & passport issue place. */
export function PlaceFields({ label, value, onChange }: { label: string; value: Place; onChange: (p: Place) => void }) {
  const isoError = value.iso !== '' && !ISO_PATTERN.test(value.iso)
    ? 'Must be 3 letters, e.g. IND (ISO alpha-3 code)' : undefined

  // Cities narrow to the chosen state once it matches a known one; otherwise suggest all.
  const cityOptions = INDIA_PLACES[value.state] ?? ALL_CITIES

  // Debounce so we don't hit the backend on every keystroke.
  const [countryQuery, setCountryQuery] = useState('')
  useEffect(() => {
    const t = setTimeout(() => setCountryQuery(value.country.trim()), 200)
    return () => clearTimeout(t)
  }, [value.country])
  const { data: countryMatches } = useGetCountriesQuery(countryQuery, { skip: countryQuery === '' })
  const countryOptions = (countryMatches ?? []).map((c) => c.name)
  const pickCountry = (name: string) => {
    const match = countryMatches?.find((c) => c.name === name)
    onChange({ ...value, country: toTitleCase(name), iso: match ? match.iso3 : value.iso })
  }

  return (
    <fieldset className="grid gap-3 rounded-lg border border-dashed border-white/50 bg-white/20 p-4 sm:grid-cols-2">
      <legend className="col-span-full mb-1 px-1 text-xs font-semibold uppercase tracking-wide text-muted">{label}</legend>
      <Input label="Location (city, state, country)" placeholder="Mumbai, Maharashtra, India" required value={value.location}
        onChange={(e) => onChange({ ...value, location: e.target.value })} className="sm:col-span-2" />
      <Autocomplete label="City" placeholder="Mumbai" value={value.city} options={cityOptions}
        onChange={(v) => onChange({ ...value, city: v })} />
      <Autocomplete label="State" placeholder="Maharashtra" value={value.state} options={INDIA_STATES}
        onChange={(v) => onChange({ ...value, state: v })} />
      <Autocomplete label="Country" placeholder="India" value={value.country} options={countryOptions}
        onChange={pickCountry} />
      <Input label="Country ISO" placeholder="IND" required maxLength={3} pattern="[A-Z]{3}" title="3-letter ISO alpha-3 code, e.g. IND"
        error={isoError} value={value.iso}
        onChange={(e) => onChange({ ...value, iso: e.target.value.toUpperCase().replace(/[^A-Z]/g, '') })} />
    </fieldset>
  )
}
