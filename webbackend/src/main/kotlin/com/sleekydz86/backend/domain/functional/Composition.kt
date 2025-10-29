package com.sleekydz86.backend.domain.functional

import reactor.core.publisher.Flux
import reactor.core.publisher.Mono

object Composition {

    fun <A, B, C> compose(
        f: (A) -> B,
        g: (B) -> C
    ): (A) -> C = { a -> g(f(a)) }

    fun <A, B, C, D> compose(
        f: (A) -> B,
        g: (B) -> C,
        h: (C) -> D
    ): (A) -> D = { a -> h(g(f(a))) }

    fun <T> pipe(vararg functions: (T) -> T): (T) -> T =
        functions.reduce { acc, func -> acc.andThen(func) }

    fun <A, B> lift(f: (A) -> B): (Mono<A>) -> Mono<B> = { mono ->
        mono.map(f)
    }

    fun <A, B> liftFlux(f: (A) -> B): (Flux<A>) -> Flux<B> = { flux ->
        flux.map(f)
    }

    fun <A, B, C> lift2(
        f: (A, B) -> C
    ): (Mono<A>, Mono<B>) -> Mono<C> = { monoA, monoB ->
        monoA.zipWith(monoB, f)
    }

    fun <A, B, C, D> lift3(
        f: (A, B, C) -> D
    ): (Mono<A>, Mono<B>, Mono<C>) -> Mono<D> = { monoA, monoB, monoC ->
        monoA.zipWith(monoB).zipWith(monoC) { (a, b), c -> f(a, b, c) }
    }

    fun <T> memoize(f: (T) -> T): (T) -> T {
        val cache = mutableMapOf<T, T>()
        return { input ->
            cache.getOrPut(input) { f(input) }
        }
    }

    fun <A, B> curry(f: (A, B) -> B): (A) -> (B) -> B = { a -> { b -> f(a, b) } }

    fun <A, B, C> curry(f: (A, B, C) -> C): (A) -> (B) -> (C) -> C =
        { a -> { b -> { c -> f(a, b, c) } } }
}