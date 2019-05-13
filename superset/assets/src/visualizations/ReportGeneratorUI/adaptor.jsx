import createAdaptor from '../../utils/createAdaptor';
import Component from './ReactReportGeneratorUI';
import transformProps from './transformProps';

export default createAdaptor(Component, transformProps);
