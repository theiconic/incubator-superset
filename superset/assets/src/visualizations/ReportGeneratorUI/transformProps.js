export default function transformProps(chartProps) {
  const { formData, payload } = chartProps;
  const { url } = formData;
  const { records } = payload.data;

  return {
    url,
    records,
  };
}
