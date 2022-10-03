const crypto = require("crypto")

const rootApiKey = crypto.randomBytes(27).toString("hex")

module.exports = {
    root_api_key: rootApiKey
}
