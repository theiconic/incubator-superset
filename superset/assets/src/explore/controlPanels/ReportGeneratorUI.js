import { t } from '@superset-ui/translation';

export default {
  controlPanelSections: [
    {
      label: t('Options'),
      expanded: true,
      controlSetRows: [
        ['url'],
      ],
    },
  ],
  controlOverrides: {
    metrics: {
      validators: [],
    },
  },
};
