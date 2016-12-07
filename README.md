# Welcome to Dropbin
Dropbin is a Python based, elegant and simple pastebin web service. It takes a
simplistic twist off hastebin.com's beautiful frontend with a little bit more
integration and added features.

## Warning!

The webservice currently hosted at https://dropb.in is very much so in beta status,
and as such, I would not recommend storing any import information within it, as
the backend and front are likely to change, and databases will be wiped prior to
its initial release out in the wild.


##### Guidelines

   * All users with accounts will have their pastes stored forever
   * All guest pastes will be stored for 2 weeks after the last time they were
     accessed


## Setup

#### Databases

Create the database to use (make sure this matches the one listed within your
configuration file) by opening a mysql command prompt `$ mysql -u root -p`:

```sql
mysql> CREATE DATABASE drop_db;
```

Generate a user to use for the database:

```sql
CREATE USER 'drop_user'@'localhost' IDENTIFIED BY 'yourpassword';
```

And last but not least, grant that user permissions for the database:

```sql
mysql> GRANT ALL PRIVILEGES ON drop_db.* TO 'drop_user'@'localhost';
```

```sql
mysql> FLUSH PRIVILEGES;
```

#### The application

Following [this guide](https://pip.pypa.io/en/latest/installing.html) to ensure
That you've got **pip** installed correctly, then once done, assuming it's linux:

```
$ sudo pip install mysql-python gunicorn
```

If you happen to run into an error when installing **mysql-python**, closely
related to `EnvironmentError: mysql_config not found`, and you're running Debian:

```
$ sudo apt-get install libmysqlclient-dev python-dev
```

Then re-run the below:

```
$ sudo pip install mysql-python gunicorn
```

Now copy the configuration file, and edit it to match the above setup:

```
$ cp example.cfg main.cfg
```

Once everything is installed, you should be able to startup the site:

```
$ gunicorn -w 4 -b 0.0.0.0:4444 app:app
```

If you happen to have any further issues, feel free to submit it with more
information [here](https://github.com/lrstanley/dropbin/issues)
