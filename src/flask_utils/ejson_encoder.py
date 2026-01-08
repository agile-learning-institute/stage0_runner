from flask.json.provider import DefaultJSONProvider as FlaskJSONProvider
import datetime

class MongoJSONEncoder(FlaskJSONProvider):
    def default(self, obj):
        if isinstance(obj, (datetime.datetime, datetime.date)):
            return str(obj)
        elif hasattr(obj, 'isoformat'):  # Handle any object with isoformat method
            return str(obj)
        return super().default(obj)

