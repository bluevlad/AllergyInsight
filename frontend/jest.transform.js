/**
 * Jest 커스텀 트랜스포머
 *
 * import.meta.env를 process.env로 변환합니다.
 */
const babelJest = require('babel-jest').default;

module.exports = babelJest.createTransformer({
  presets: [
    ['@babel/preset-env', { targets: { node: 'current' } }],
    ['@babel/preset-react', { runtime: 'automatic' }],
  ],
  plugins: [
    // import.meta.env를 process.env로 변환
    function transformImportMeta() {
      return {
        visitor: {
          MetaProperty(path) {
            // import.meta.env.XXX -> process.env.XXX
            if (
              path.node.meta.name === 'import' &&
              path.node.property.name === 'meta'
            ) {
              path.replaceWithSourceString('process.env');
            }
          },
        },
      };
    },
  ],
});
