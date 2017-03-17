var promise = require('bluebird');
var josm = require('../../metrics/josm_edits.js');

exports.up = function (knex, Promise) {
  return knex.schema.table('users', function (table) {
    table.decimal('total_josm_edit_count', 40, 20);

    // Fill users table
    knex('changesets').select('id', 'user_id', 'editor')
    .then(function (results) {
      results = results.filter(function (result) {
        return result.editor && josm(result.editor) === 1;
      });
      promise.map(results, function (result) {
        return knex('users')
        .where('user_id', result.user_id)
        .increment('total_josm_edit_count', 1);
      });
    });
  });
};

exports.down = function (knex, Promise) {
  return knex.schema.table('users', function (table) {
    table.dropColumn('total_josm_edit_count');
  });
};
