import PropTypes from 'prop-types';
import './ReportGeneratorUI.css';
import { clearChildren, openUrlInNewTab } from './Util';

const REPORT_SERVICE_BASE_URL = 'https://report-generator.live.ambo.eks.aws.theiconic.com.au/';
const REPORT_SERVICE_GENERATE_PATH = 'generate-report/best-sellers/v1/';

const propTypes = {
  // Each object is { field1: value1, field2: value2 }
  data: PropTypes.arrayOf(PropTypes.object),
  height: PropTypes.number,
  alignPositiveNegative: PropTypes.bool,
  colorPositiveNegative: PropTypes.bool,
  columns: PropTypes.arrayOf(PropTypes.shape({
    key: PropTypes.string,
    label: PropTypes.string,
    format: PropTypes.string,
  })),
  filters: PropTypes.object,
  includeSearch: PropTypes.bool,
  metrics: PropTypes.arrayOf(PropTypes.oneOfType([
    PropTypes.string,
    PropTypes.object,
  ])),
  onAddFilter: PropTypes.func,
  onRemoveFilter: PropTypes.func,
  orderDesc: PropTypes.bool,
  pageLength: PropTypes.oneOfType([
    PropTypes.number,
    PropTypes.string,
  ]),
  percentMetrics: PropTypes.arrayOf(PropTypes.oneOfType([
    PropTypes.string,
    PropTypes.object,
  ])),
  tableFilter: PropTypes.bool,
  tableTimestampFormat: PropTypes.string,
  timeseriesLimitMetric: PropTypes.oneOfType([
    PropTypes.string,
    PropTypes.object,
  ]),
};

async function ReportGeneratorUIVis(element, props) {
  console.log(props);
  const {
    data,
    // columns,
  } = props;
  clearChildren(element);
  const generateReportEl = document.createElement('button');
  generateReportEl.innerText = 'Generate Report';
  generateReportEl.addEventListener('click', async () => {
    const payload = {
      query: '',
      rowcount: data.length,
      status: 'success',
      data: {
        records: data,
        columns: [],
      },
    };

    const fetchOptions = {
      method: 'post',
      headers: {
        Accept: 'application/json',
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(payload),
    };

    const response = await fetch(
      `${REPORT_SERVICE_BASE_URL}${REPORT_SERVICE_GENERATE_PATH}`,
      fetchOptions,
    );
    const responseContent = await response.json();
    const openSucceeded = openUrlInNewTab(responseContent.reportUrl);

    if (openSucceeded) {
      return;
    }

    const reportLink = document.createElement('a');
    reportLink.href = responseContent.reportUrl;
    reportLink.innerText = 'Open Generated Report';
    reportLink.setAttribute('target', '_blank');
    element.appendChild(reportLink);
  });

  element.appendChild(generateReportEl);
}

ReportGeneratorUIVis.displayName = 'ReportGeneratorUIVis';
ReportGeneratorUIVis.propTypes = propTypes;

export default ReportGeneratorUIVis;
