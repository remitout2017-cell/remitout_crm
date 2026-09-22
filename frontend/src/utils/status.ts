import type { Tone } from '../components/ui/Badge'

/** Maps a backend status string to a tone. */
export const statusTone = (s: string): Tone =>
  /complete|success|active|approved|done/i.test(s) ? 'green' : /fail|reject|error|inactive/i.test(s) ? 'red' : /pending|draft|progress|new/i.test(s) ? 'brand' : 'gray'
