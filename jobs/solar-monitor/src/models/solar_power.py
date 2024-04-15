from pydantic import BaseModel

class SolarPower(BaseModel):
    current_production: float
    current_consumption: float

    def __repr__(self):
        return f"Net: {self.net:.2f} ({self.current_production:.2f} - {self.current_consumption:.2f})"

    """A property for calculating the net power"""
    @property
    def net(self):
        return self.current_production - self.current_consumption
