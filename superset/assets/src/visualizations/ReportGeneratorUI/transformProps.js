export default function transformProps(chartProps) {
  const { formData, payload } = chartProps;
  const { url } = formData;
  const { records, columns } = payload.data;

  return {
    url,
    records,
    columns,
  };
}
