from Airport import Airport
import random
from plots import (
    plot_passengers_in_airport,
    plot_id_queues,
    plot_security_congestion,
    plot_boarding_queue,
)


def main():
    airportGates = 10
    airport = Airport(
        num_gates=airportGates,

        regular_id_servers=6,
        precheck_id_servers=1,
        clear_id_servers=1,

        id_service_rate=1 / .5,
        precheck_service_rate=1 / 0.50,
        clear_service_rate=1 / 0.35,

        num_regular_security_lanes=5,
        regular_security_service_rate=1 / 0.5,
        regular_security_capacity=12,

        num_precheck_security_lanes=2,
        precheck_security_service_rate=1 / 0.5,
        precheck_security_capacity=10,

        boarding_service_rate=1 / 0.20
    )

    number_of_flights=random.randint(airportGates * 6, airportGates*10)
    # An airport gate typically handles 6 to 10 flights per day on average
    airport.seed_flights(
        num_flights=number_of_flights,
        start_time=180,
        end_time=1440
    )

    airport.run(max_time=1500)

    metrics = airport.compute_metrics()

    print("\nAirport Simulation Metrics")
    print("--------------------------")
    for key, value in metrics.items():
        print(f"{key}: {value}")
    print(f"\nNumber of flights Today: {number_of_flights}")
    
    plot_passengers_in_airport(airport.time_series)
    plot_id_queues(airport.time_series)
    plot_security_congestion(airport.time_series)
    plot_boarding_queue(airport.time_series)


if __name__ == "__main__":
    main()