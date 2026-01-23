import Plot from 'react-plotly.js';

interface ChartRendererProps {
  spec: any;
}

const ChartRenderer: React.FC<ChartRendererProps> = ({ spec }) => {
  if (!spec || !spec.data) {
    return null;
  }

  return (
    <div className="w-full bg-white rounded-lg shadow-sm border border-gray-200 p-4 my-4">
      <Plot
        data={spec.data}
        layout={{
          ...spec.layout,
          autosize: true,
          responsive: true,
        }}
        config={{
          responsive: true,
          displayModeBar: true,
          displaylogo: false,
          modeBarButtonsToRemove: ['lasso2d', 'select2d'],
        }}
        style={{ width: '100%', height: '100%' }}
        useResizeHandler={true}
      />
    </div>
  );
};

export default ChartRenderer;
