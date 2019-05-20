import { t } from '@superset-ui/translation';
import { ChartMetadata, ChartPlugin } from '@superset-ui/chart';
import transformProps from './transformProps';
import { ANNOTATION_TYPES } from '../../modules/AnnotationTypes';

const metadata = new ChartMetadata({
  name: t('Report Generator UI'),
  description: '',
  canBeAnnotationTypes: [
    ANNOTATION_TYPES.EVENT,
    ANNOTATION_TYPES.INTERVAL,
  ],
});

export default class TableChartPlugin extends ChartPlugin {
  constructor() {
    super({
      metadata,
      transformProps,
      loadChart: () => import('./ReactReportGeneratorUI.js'),
    });
  }
}
