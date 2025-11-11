import { useQuery } from '@tanstack/react-query';
import { api } from '@/services/api';
import { FileText, Clock, CheckCircle, AlertCircle, Flag } from 'lucide-react';

export default function DashboardPage() {
  const { data: stats, isLoading } = useQuery({
    queryKey: ['documentStats'],
    queryFn: () => api.getDocumentStats(),
  });

  if (isLoading) {
    return <div className="text-center py-12">Loading...</div>;
  }

  const statCards = [
    { label: 'Total Documents', value: stats?.total_documents || 0, icon: FileText, color: 'blue' },
    { label: 'Completed', value: stats?.completed || 0, icon: CheckCircle, color: 'green' },
    { label: 'Processing', value: stats?.processing || 0, icon: Clock, color: 'yellow' },
    { label: 'Flagged', value: stats?.flagged || 0, icon: Flag, color: 'red' },
    { label: 'Failed', value: stats?.failed || 0, icon: AlertCircle, color: 'red' },
  ];

  return (
    <div className="px-4 py-6">
      <h1 className="text-3xl font-bold text-gray-900 mb-8">Dashboard</h1>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-6 mb-8">
        {statCards.map((stat) => (
          <div key={stat.label} className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">{stat.label}</p>
                <p className="text-3xl font-bold mt-2">{stat.value}</p>
              </div>
              <stat.icon className={`h-12 w-12 text-${stat.color}-500`} />
            </div>
          </div>
        ))}
      </div>

      {stats?.avg_processing_time_seconds && (
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-xl font-semibold mb-4">Performance</h2>
          <div className="text-lg">
            Average Processing Time:{' '}
            <span className="font-bold">{stats.avg_processing_time_seconds.toFixed(2)}s</span>
          </div>
        </div>
      )}
    </div>
  );
}
