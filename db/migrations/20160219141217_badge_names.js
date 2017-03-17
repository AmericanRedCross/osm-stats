exports.up = function (knex, Promise) {
  return Promise.all([
    knex('badges').where('name', 'Point Creator').update({'name': 'On Point'}),
    knex('badges').where('name', 'Building Builder').update({'name': 'The Wright Stuff'}),
    knex('badges').where('name', 'GPS Trace Creator').update({'name': 'Field Mapper'}),
    knex('badges').where('name', 'Long & Winding Road').update({'name': 'On The Road Again'}),
    knex('badges').where('name', 'Long & Winding Road Maintainer').update({'name': 'Long and Winding Road'}),
    knex('badges').where('name', 'Waterway Creator').update({'name': 'White Water Rafting'}),
    knex('badges').where('name', 'TaskMan Square Champion').update({'name': 'Task Champion'}),
    knex('badges').where('name', 'TaskMan Scrutinizer').update({'name': 'Scrutinizer'}),
    knex('badges').where('name', 'JOSM User').update({'name': 'Awesome JOSM'})
  ]);
};

exports.down = function (knex, Promise) {
  return Promise.all([
    knex('badges').where('name', 'On Point').update({'name': 'Point Creator'}),
    knex('badges').where('name', 'The Wright Stuff').update({'name': 'Building Builder'}),
    knex('badges').where('name', 'Field Mapper').update({'name': 'GPS Trace Creator'}),
    knex('badges').where('name', 'On The Road Again').update({'name': 'Long & Winding Road'}),
    knex('badges').where('name', 'Long and Winding Road').update({'name': 'Long & Winding Road Maintainer'}),
    knex('badges').where('name', 'White Water Rafting').update({'name': 'Waterway Creator'}),
    knex('badges').where('name', 'Task Champion').update({'name': 'TaskMan Square Champion'}),
    knex('badges').where('name', 'Scrutinizer').update({'name': 'TaskMan Scrutinizer'}),
    knex('badges').where('name', 'Awesome JOSM').update({'name': 'JOSM User'})
  ]);
};
