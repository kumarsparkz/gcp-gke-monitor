import React from 'react';

interface Column {
  key: string;
  label: string;
  render?: (value: any, row: any) => React.ReactNode;
}

interface MetricsTableProps {
  title: string;
  columns: Column[];
  data: any[];
  emptyMessage?: string;
}

export const MetricsTable: React.FC<MetricsTableProps> = ({
  title,
  columns,
  data,
  emptyMessage = 'No issues detected',
}) => {
  if (data.length === 0) {
    return (
      <div style={styles.section}>
        <h2 style={styles.title}>{title}</h2>
        <p style={styles.emptyMessage}>{emptyMessage}</p>
      </div>
    );
  }

  return (
    <div style={styles.section}>
      <h2 style={styles.title}>{title}</h2>
      <div style={styles.tableContainer}>
        <table style={styles.table}>
          <thead>
            <tr>
              {columns.map((col) => (
                <th key={col.key} style={styles.th}>
                  {col.label}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {data.map((row, index) => (
              <tr key={index} style={styles.tr}>
                {columns.map((col) => (
                  <td key={col.key} style={styles.td}>
                    {col.render ? col.render(row[col.key], row) : row[col.key]}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

const styles: { [key: string]: React.CSSProperties } = {
  section: {
    marginBottom: '30px',
    backgroundColor: '#1e1e1e',
    padding: '20px',
    borderRadius: '8px',
    border: '1px solid #333',
  },
  title: {
    fontSize: '20px',
    fontWeight: 'bold',
    marginBottom: '15px',
    color: '#ffffff',
  },
  emptyMessage: {
    color: '#4ade80',
    fontSize: '14px',
  },
  tableContainer: {
    overflowX: 'auto',
  },
  table: {
    width: '100%',
    borderCollapse: 'collapse',
    fontSize: '14px',
  },
  th: {
    backgroundColor: '#2a2a2a',
    color: '#ffffff',
    padding: '12px',
    textAlign: 'left',
    fontWeight: '600',
    borderBottom: '2px solid #444',
  },
  tr: {
    borderBottom: '1px solid #333',
  },
  td: {
    padding: '12px',
    color: '#e5e5e5',
  },
};
