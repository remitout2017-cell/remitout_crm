import { FiRefreshCw } from 'react-icons/fi'
import { Button } from '../../components/ui/Button'
import { Card } from '../../components/ui/Card'
import { useGetFormDataQuery } from '../reference/api'

/** Edubao's "Get Form Required Data" (app types, titles, document types) for the lead's partner account. */
export function ReferencePanel({ partnerAccountId }: { partnerAccountId: number }) {
  const { data, isLoading, isFetching, refetch } = useGetFormDataQuery(partnerAccountId)

  return (
    <Card title="Form required data" action={
      <Button variant="secondary" icon={<FiRefreshCw className={isFetching ? 'animate-spin' : undefined} />} onClick={() => refetch()}>
        Refresh
      </Button>
    }>
      <p className="mb-3 text-sm text-muted">
        App types, titles and document type codes accepted by Edubao — use these values for <code>app_type</code>{' '}
        and <code>visa_eligibility_doc_type</code> above.
      </p>
      {isLoading && <div className="h-32 animate-pulse rounded-lg bg-white/40" />}
      {!isLoading && (
        <pre className="max-h-96 overflow-auto rounded-lg border border-white/40 bg-white/25 p-3 text-xs">
          {JSON.stringify(data ?? {}, null, 2)}
        </pre>
      )}
    </Card>
  )
}
